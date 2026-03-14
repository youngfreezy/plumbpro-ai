"""Agent session lifecycle and SSE streaming routes.

Handles:
  - POST /api/agent/session                       -- Start agent session
  - GET  /api/agent/session/{session_id}           -- Get session state
  - GET  /api/agent/session/{session_id}/stream    -- SSE event stream (with replay)
  - POST /api/agent/session/{session_id}/message   -- Send follow-up message
  - POST /api/agent/session/{session_id}/approve   -- HITL approval
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.shared.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent"])


# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

# Session metadata saved at creation time
session_registry: Dict[str, dict] = {}

# Append-only event log per session for SSE replay on reconnect.
event_logs: Dict[str, list] = {}

# Per-session list of subscriber queues (one per connected SSE client).
sse_subscribers: Dict[str, List[asyncio.Queue]] = {}

# Strong references to background tasks to prevent GC
_background_tasks: set[asyncio.Task[Any]] = set()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class StartSessionRequest(BaseModel):
    module: Optional[str] = None  # Optional: diagnostic | quoting | scheduling | routing | None (auto-detect)
    message: str                   # User's initial message / request
    job_id: Optional[str] = None   # Optionally tie session to a job


class SendMessageRequest(BaseModel):
    message: str


class ApproveRequest(BaseModel):
    approved: bool
    modifications: Optional[dict] = None  # Optional changes before approval


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize(obj: Any) -> Any:
    """Make an object JSON-safe (handles Pydantic models, datetimes, etc.)."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj


async def _emit(session_id: str, event_type: str, data: dict) -> None:
    """Log an SSE event and push it to all active subscribers."""
    event = {"type": event_type, "data": data}

    # Append to persistent event log for replay
    if session_id in event_logs:
        event_logs[session_id].append(event)

    # Push to all connected SSE clients
    for queue in sse_subscribers.get(session_id, []):
        await queue.put(event)


def _set_session_status(session_id: str, status: str) -> None:
    """Update session status in both in-memory registry and Postgres."""
    if session_id in session_registry:
        session_registry[session_id]["status"] = status

    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE agent_sessions SET status = %s, updated_at = %s WHERE id = %s",
                (status, datetime.now(timezone.utc), session_id),
            )
            conn.commit()
    except Exception:
        logger.debug("Failed to update session status in DB for %s", session_id, exc_info=True)


def _spawn_background(coro: Any) -> asyncio.Task[Any]:
    """Create and retain a background task until completion."""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


def _require_auth(request: Request) -> tuple[str, str, str]:
    """Extract user_email, user_id, and company_id from request state."""
    email = getattr(request.state, "user_email", None)
    user_id = getattr(request.state, "user_id", None)
    company_id = getattr(request.state, "company_id", None)
    if not email or not company_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return email, user_id or "", company_id


# ---------------------------------------------------------------------------
# Status messages for PlumbPro AI modules
# ---------------------------------------------------------------------------

STATUS_MESSAGES = {
    "intake": "Setting up your session...",
    "analyzing": "Analyzing your request...",
    "diagnosing": "Running diagnostic analysis...",
    "quoting": "Generating quote...",
    "scheduling": "Working on scheduling...",
    "routing": "Optimizing routes...",
    "awaiting_approval": "Waiting for your approval...",
    "executing": "Executing approved actions...",
    "completed": "All done!",
    "failed": "Something went wrong -- check the details below",
}


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

async def _run_agent_pipeline(
    session_id: str,
    module: Optional[str],
    message: str,
    graph: Any,
    user_id: str,
    company_id: str,
    job_id: Optional[str] = None,
) -> None:
    """Execute the LangGraph router and emit SSE events.

    Runs as a background task so the POST response returns immediately.
    """
    from backend.shared.event_bus import register_emitter, unregister_emitter

    register_emitter(session_id, _emit)

    try:
        initial_state: Dict[str, Any] = {
            "session_id": session_id,
            "user_id": user_id,
            "company_id": company_id,
            "module": module,
            "message": message,
            "job_id": job_id,
            "status": "intake",
            "messages": [],
            "agent_outputs": {},
            "errors": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        await _emit(session_id, "status", {
            "status": "intake",
            "message": "Starting your session...",
        })

        config = {"configurable": {"thread_id": session_id}}

        # Stream graph execution
        async for chunk in graph.astream(
            initial_state, config=config, stream_mode="values", version="v2"
        ):
            await asyncio.sleep(0)  # Yield to event loop

            state_snapshot = chunk["data"]
            interrupts = chunk.get("interrupts", ())
            status = state_snapshot.get("status", "unknown")

            _set_session_status(session_id, status)

            # Emit status update
            await _emit(session_id, "status", {
                "status": status,
                "message": STATUS_MESSAGES.get(status, status),
                "agent_outputs": _serialize(state_snapshot.get("agent_outputs", {})),
            })

            # Emit module-specific events
            if status == "diagnosing" and state_snapshot.get("diagnosis"):
                await _emit(session_id, "diagnosis", {
                    "status": "diagnosing",
                    "diagnosis": _serialize(state_snapshot["diagnosis"]),
                })

            if status == "quoting" and state_snapshot.get("quote"):
                await _emit(session_id, "quote", {
                    "status": "quoting",
                    "quote": _serialize(state_snapshot["quote"]),
                })

            if status == "awaiting_approval":
                await _emit(session_id, "hitl", {
                    "status": "awaiting_approval",
                    "pending_action": _serialize(state_snapshot.get("pending_action", {})),
                    "message": "Please review and approve the proposed action.",
                })

            # Terminal states
            if status in ("completed", "failed"):
                await _emit(session_id, "done", {
                    "status": status,
                    "summary": _serialize(state_snapshot.get("summary")),
                })
                unregister_emitter(session_id)
                return

            # Handle interrupts (HITL gates)
            if interrupts:
                for intr in interrupts:
                    stage = intr.value.get("stage") if isinstance(intr.value, dict) else None
                    if stage:
                        logger.info("Agent paused at '%s' for session %s", stage, session_id)
                        _set_session_status(session_id, "awaiting_approval")
                        await _emit(session_id, "hitl", {
                            "status": "awaiting_approval",
                            "stage": stage,
                            "pending_action": _serialize(
                                intr.value.get("data", {})
                            ),
                            "message": "Approval needed to continue.",
                        })
                        # Don't unregister -- pipeline will resume after approval
                        return

    except Exception as exc:
        logger.exception("Agent pipeline error for session %s", session_id)
        _set_session_status(session_id, "failed")
        await _emit(session_id, "error", {
            "message": "An internal error occurred",
            "session_id": session_id,
        })
        await _emit(session_id, "done", {
            "status": "failed",
            "error": str(exc),
        })
        unregister_emitter(session_id)


async def _resume_agent_pipeline(
    session_id: str,
    graph: Any,
    resume_value: Any = None,
) -> None:
    """Resume the pipeline after an interrupt (HITL approval)."""
    from backend.shared.event_bus import register_emitter, unregister_emitter
    from langgraph.types import Command

    register_emitter(session_id, _emit)
    config: dict = {"configurable": {"thread_id": session_id}}
    resume_input = Command(resume=resume_value) if resume_value is not None else None

    try:
        async for chunk in graph.astream(
            resume_input, config=config, stream_mode="values", version="v2"
        ):
            await asyncio.sleep(0)

            state_snapshot = chunk["data"]
            interrupts = chunk.get("interrupts", ())
            status = state_snapshot.get("status", "unknown")

            _set_session_status(session_id, status)

            await _emit(session_id, "status", {
                "status": status,
                "message": STATUS_MESSAGES.get(status, status),
                "agent_outputs": _serialize(state_snapshot.get("agent_outputs", {})),
            })

            if status in ("completed", "failed"):
                await _emit(session_id, "done", {
                    "status": status,
                    "summary": _serialize(state_snapshot.get("summary")),
                })
                unregister_emitter(session_id)
                return

            if interrupts:
                for intr in interrupts:
                    stage = intr.value.get("stage") if isinstance(intr.value, dict) else None
                    if stage:
                        _set_session_status(session_id, "awaiting_approval")
                        await _emit(session_id, "hitl", {
                            "status": "awaiting_approval",
                            "stage": stage,
                            "pending_action": _serialize(intr.value.get("data", {})),
                            "message": "Approval needed to continue.",
                        })
                        return

    except Exception as exc:
        logger.exception("Agent pipeline resume error for session %s", session_id)
        _set_session_status(session_id, "failed")
        await _emit(session_id, "error", {
            "message": "An internal error occurred",
            "session_id": session_id,
        })
        await _emit(session_id, "done", {
            "status": "failed",
            "error": str(exc),
        })
    finally:
        if session_registry.get(session_id, {}).get("status") in {"completed", "failed"}:
            from backend.shared.event_bus import unregister_emitter
            unregister_emitter(session_id)


# ---------------------------------------------------------------------------
# SSE event generator
# ---------------------------------------------------------------------------

async def _event_generator(session_id: str, checkpointer=None, graph=None):
    """Yield SSE frames: first replay stored events, then stream live.

    Each connected client gets its own subscriber queue so multiple tabs
    or reconnects work independently.
    """
    subscriber_queue: asyncio.Queue = asyncio.Queue()
    if session_id not in sse_subscribers:
        sse_subscribers[session_id] = []
    sse_subscribers[session_id].append(subscriber_queue)

    try:
        stored = list(event_logs.get(session_id, []))

        # Phase 0: If no stored events, synthesise from checkpointer
        if not stored and checkpointer is not None:
            async for frame in _synthesise_snapshot(session_id, checkpointer, graph):
                yield frame
                if "event: done\n" in frame:
                    return

        # Phase 1: Replay all previously stored events
        for event in stored:
            event_type = event.get("type", "message")
            event_data = json.dumps(event.get("data", {}))
            yield f"event: {event_type}\ndata: {event_data}\n\n"
            if event_type == "done":
                return

        # Phase 2: Stream new live events from the subscriber queue
        while True:
            try:
                event = await asyncio.wait_for(subscriber_queue.get(), timeout=25)
                event_type = event.get("type", "message")
                event_data = json.dumps(event.get("data", {}))

                yield f"event: {event_type}\ndata: {event_data}\n\n"

                if event_type == "done":
                    break
            except asyncio.TimeoutError:
                yield 'event: ping\ndata: ""\n\n'
    finally:
        subs = sse_subscribers.get(session_id, [])
        if subscriber_queue in subs:
            subs.remove(subscriber_queue)


async def _synthesise_snapshot(session_id: str, checkpointer, graph=None):
    """Yield synthetic SSE events from durable checkpoint state.

    Called when event_logs is empty (backend restarted) so the frontend
    can hydrate without having received the original live events.
    """
    try:
        config = {"configurable": {"thread_id": session_id}}
        state = await checkpointer.aget(config)
        if state is None:
            return

        cp = state
        if hasattr(state, "checkpoint"):
            cp = state.checkpoint
        cv = cp.get("channel_values", cp) if isinstance(cp, dict) else cp
        if not isinstance(cv, dict):
            return

        status = cv.get("status", "unknown")

        # Check for HITL interrupts
        if graph is not None:
            try:
                graph_state = await graph.aget_state(config)
                next_nodes = getattr(graph_state, "next", ()) or ()
                if any("approval" in n for n in next_nodes):
                    status = "awaiting_approval"
            except Exception:
                logger.debug("Could not check interrupt status for %s", session_id)

        _set_session_status(session_id, status)

        # Emit status
        status_data = {
            "status": status,
            "message": STATUS_MESSAGES.get(status, status),
        }
        yield f"event: status\ndata: {json.dumps(_serialize(status_data))}\n\n"

        # Emit HITL event if awaiting approval
        if status == "awaiting_approval":
            hitl_data = {
                "status": "awaiting_approval",
                "pending_action": _serialize(cv.get("pending_action", {})),
                "message": "Approval needed to continue.",
            }
            yield f"event: hitl\ndata: {json.dumps(hitl_data)}\n\n"

        # Emit done for terminal sessions
        if status in ("completed", "failed"):
            done_data = {
                "status": status,
                "summary": _serialize(cv.get("summary")),
            }
            yield f"event: done\ndata: {json.dumps(done_data)}\n\n"

    except Exception:
        logger.exception("Failed to synthesise snapshot for session %s", session_id)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/session")
async def start_session(body: StartSessionRequest, request: Request):
    """Create a new agent session and begin execution in the background."""
    email, user_id, company_id = _require_auth(request)

    session_id = str(uuid.uuid4())
    graph = request.app.state.graph
    now = datetime.now(timezone.utc)

    # Initialize in-memory stores
    event_logs[session_id] = []
    sse_subscribers[session_id] = []

    # Register session metadata
    session_meta = {
        "session_id": session_id,
        "user_id": user_id,
        "user_email": email,
        "company_id": company_id,
        "module": body.module,
        "status": "intake",
        "job_id": body.job_id,
        "created_at": now.isoformat(),
    }
    session_registry[session_id] = session_meta

    # Persist to DB
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO agent_sessions (
                id, company_id, user_id, module, status, job_id, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (session_id, company_id, user_id, body.module, "intake", body.job_id, now, now),
        )
        conn.commit()

    # Spawn background pipeline task
    _spawn_background(
        _run_agent_pipeline(
            session_id=session_id,
            module=body.module,
            message=body.message,
            graph=graph,
            user_id=user_id,
            company_id=company_id,
            job_id=body.job_id,
        )
    )

    logger.info("Started agent session %s (module=%s) for %s", session_id, body.module, email)

    return {
        "session_id": session_id,
        "status": "intake",
        "module": body.module,
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str, request: Request):
    """Get current session state."""
    email, user_id, company_id = _require_auth(request)

    # Check in-memory registry first
    meta = session_registry.get(session_id)
    if meta:
        if meta.get("company_id") != company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        return {"session": _serialize(meta)}

    # Fall back to DB
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM agent_sessions WHERE id = %s AND company_id = %s",
            (session_id, company_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        cols = [col.name for col in cur.description]
        session = dict(zip(cols, row))

    return {"session": _serialize(session)}


@router.get("/session/{session_id}/stream")
async def stream_session(session_id: str, request: Request):
    """SSE stream for a session. Replays past events first, then streams live."""
    # Auth: check token from query param (EventSource can't set headers)
    email = getattr(request.state, "user_email", None)
    company_id = getattr(request.state, "company_id", None)

    if not email or not company_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Verify session belongs to this company
    meta = session_registry.get(session_id)
    if meta and meta.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not meta:
        # Check DB
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT id FROM agent_sessions WHERE id = %s AND company_id = %s",
                (session_id, company_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Session not found")

    checkpointer = getattr(request.app.state, "checkpointer", None)
    graph = getattr(request.app.state, "graph", None)

    return StreamingResponse(
        _event_generator(session_id, checkpointer=checkpointer, graph=graph),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/session/{session_id}/message")
async def send_message(session_id: str, body: SendMessageRequest, request: Request):
    """Send a follow-up message to the agent session."""
    email, user_id, company_id = _require_auth(request)

    meta = session_registry.get(session_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Session not found")
    if meta.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    terminal_statuses = {"completed", "failed"}
    if meta.get("status") in terminal_statuses:
        raise HTTPException(status_code=400, detail="Session has ended")

    graph = request.app.state.graph

    # Emit the user message as an SSE event
    await _emit(session_id, "user_message", {
        "message": body.message,
        "user_email": email,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Send message to the graph via Command
    from langgraph.types import Command

    _spawn_background(
        _resume_agent_pipeline(
            session_id=session_id,
            graph=graph,
            resume_value={"type": "message", "content": body.message},
        )
    )

    return {"ok": True, "session_id": session_id}


@router.post("/session/{session_id}/approve")
async def approve_action(session_id: str, body: ApproveRequest, request: Request):
    """HITL approval: approve or reject a pending agent action."""
    email, user_id, company_id = _require_auth(request)

    meta = session_registry.get(session_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Session not found")
    if meta.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if meta.get("status") != "awaiting_approval":
        raise HTTPException(status_code=400, detail="Session is not awaiting approval")

    graph = request.app.state.graph

    if body.approved:
        _set_session_status(session_id, "executing")
        await _emit(session_id, "status", {
            "status": "executing",
            "message": "Approved. Executing...",
        })

        resume_value = {
            "type": "approval",
            "approved": True,
            "modifications": body.modifications,
        }
    else:
        _set_session_status(session_id, "completed")
        await _emit(session_id, "status", {
            "status": "completed",
            "message": "Action was rejected.",
        })
        await _emit(session_id, "done", {
            "status": "completed",
            "message": "Session ended -- action was rejected by user.",
        })
        return {"ok": True, "session_id": session_id, "action": "rejected"}

    _spawn_background(
        _resume_agent_pipeline(
            session_id=session_id,
            graph=graph,
            resume_value=resume_value,
        )
    )

    logger.info("Session %s approved by %s", session_id, email)
    return {"ok": True, "session_id": session_id, "action": "approved"}
