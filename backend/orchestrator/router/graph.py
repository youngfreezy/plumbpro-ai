"""Thin LangGraph router for PlumbPro AI.

This is intentionally minimal — the real intelligence lives inside each
module's ReAct agent (see ``base_agent.run_react_agent``).  The graph
does three things:

  1. **classify_request** — Use the light model to figure out which module
     should handle the request.
  2. **run_module** — Delegate to the appropriate module's ReAct agent.
  3. **check_hitl** — Decide whether the result needs human approval
     before being finalised.

The graph is compiled with ``interrupt_before=["check_hitl"]`` so the
gateway layer can pause execution and wait for human confirmation when
necessary (e.g., before sending an estimate to a customer).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from backend.orchestrator.modules.base_agent import run_react_agent
from backend.orchestrator.router.state import PlumbProState
from backend.shared.event_bus import emit_agent_event
from backend.shared.llm import get_light_model, invoke_with_retry

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Module registry — maps module names to their agent config loaders.
# Each entry must expose get_system_prompt() and get_tools().
# -----------------------------------------------------------------------
_MODULE_REGISTRY: Dict[str, str] = {
    "scheduling": "backend.orchestrator.modules.scheduling.agent",
    "diagnostics": "backend.orchestrator.modules.diagnostics.agent",
    "estimates": "backend.orchestrator.modules.estimates.agent",
    "inventory": "backend.orchestrator.modules.inventory.agent",
    "communication": "backend.orchestrator.modules.communication.agent",
    "permits": "backend.orchestrator.modules.permits.agent",
    "documentation": "backend.orchestrator.modules.documentation.agent",
    "training": "backend.orchestrator.modules.training.agent",
}

# Modules whose output must be reviewed by a human before finalising.
_HITL_MODULES = {"estimates", "permits", "communication"}

def _build_classification_prompt() -> str:
    """Build the classification prompt using domain config."""
    from backend.shared.domain_config import get_domain_config

    cfg = get_domain_config()
    tech_label = cfg.labels.get("technician", "Technician").lower()
    job_label = cfg.labels.get("job", "Service Call").lower()
    part_label = cfg.labels.get("part", "Part").lower()

    # Build module descriptions using domain-specific terminology
    module_lines = []
    module_descriptions = {
        "scheduling": f"{job_label} scheduling, dispatching, {tech_label} availability, appointments, rescheduling",
        "diagnostics": f"Troubleshooting {cfg.business_type} issues, diagnostic guidance, repair recommendations",
        "estimates": "Cost estimates, quotes, pricing, invoices",
        "inventory": f"{part_label}s, supplies, stock levels, ordering materials",
        "communication": "Customer notifications, emails, SMS, follow-ups",
        "permits": "Building permits, inspections, compliance, code requirements",
        "documentation": f"{job_label} reports, photos, notes, work orders, documentation",
        "training": f"{tech_label} training, procedures, best practices, safety protocols",
    }

    for module_name in _MODULE_REGISTRY:
        if module_name in cfg.enabled_modules:
            desc = module_descriptions.get(module_name, module_name)
            module_lines.append(f"- {module_name}: {desc}")

    modules_text = "\n".join(module_lines)

    return f"""\
You are a request classifier for a {cfg.business_type} business management platform ({cfg.app_name}).

Given the user's request, classify it into exactly ONE of these modules:
{modules_text}

Respond with ONLY a JSON object: {{"module": "<module_name>", "confidence": <0.0-1.0>}}
Do NOT include any other text.
"""


_CLASSIFICATION_PROMPT: str | None = None


def _load_module(module_name: str) -> Any:
    """Dynamically import a module agent by dotted path."""
    import importlib

    dotted = _MODULE_REGISTRY.get(module_name)
    if dotted is None:
        raise ValueError(
            f"Unknown module '{module_name}'. "
            f"Available: {list(_MODULE_REGISTRY.keys())}"
        )
    return importlib.import_module(dotted)


# -----------------------------------------------------------------------
# Graph nodes
# -----------------------------------------------------------------------


async def classify_request(state: PlumbProState) -> Dict[str, Any]:
    """Use the light model to classify the user's request into a module."""
    session_id = state["session_id"]
    request = state["request"]

    logger.info("[Router] classifying request: %s", request[:200])

    if session_id:
        await emit_agent_event(session_id, "classifying", {
            "request": request[:200],
        })

    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_light_model()
    global _CLASSIFICATION_PROMPT
    if _CLASSIFICATION_PROMPT is None:
        _CLASSIFICATION_PROMPT = _build_classification_prompt()

    messages = [
        SystemMessage(content=_CLASSIFICATION_PROMPT),
        HumanMessage(content=request),
    ]

    try:
        response = await invoke_with_retry(llm, messages)
        content = response.content.strip()

        # Parse the JSON response
        parsed = json.loads(content)
        module = parsed["module"]
        confidence = parsed.get("confidence", 0.0)

        if module not in _MODULE_REGISTRY:
            logger.warning(
                "[Router] classifier returned unknown module '%s', "
                "falling back to 'scheduling'",
                module,
            )
            module = "scheduling"
            confidence = 0.0

        logger.info(
            "[Router] classified as module='%s' confidence=%.2f",
            module,
            confidence,
        )

        if session_id:
            await emit_agent_event(session_id, "classified", {
                "module": module,
                "confidence": confidence,
            })

        return {
            "module": module,
            "context": {"classification_confidence": confidence},
            "status": "running",
        }

    except (json.JSONDecodeError, KeyError) as exc:
        logger.error("[Router] classification parse error: %s", exc)
        # Fallback to scheduling for unparseable responses
        return {
            "module": "scheduling",
            "context": {"classification_confidence": 0.0, "classification_error": str(exc)},
            "status": "running",
        }


async def run_module(state: PlumbProState) -> Dict[str, Any]:
    """Load the target module's agent and run the ReAct loop."""
    module_name = state["module"]
    session_id = state["session_id"]
    request = state["request"]

    logger.info("[Router] running module '%s'", module_name)

    if session_id:
        await emit_agent_event(session_id, "module_started", {
            "module": module_name,
        })

    try:
        mod = _load_module(module_name)
    except (ValueError, ImportError) as exc:
        logger.error("[Router] failed to load module '%s': %s", module_name, exc)
        return {
            "result": {
                "status": "error",
                "result": f"Module '{module_name}' is not available yet: {exc}",
                "tool_calls_made": [],
            },
            "status": "error",
        }

    system_prompt = mod.get_system_prompt()
    tools = mod.get_tools()

    # Build context from state
    agent_context = {
        "company_id": state.get("company_id"),
        "user_id": state.get("user_id"),
        "job_id": state.get("job_id"),
        "customer_id": state.get("customer_id"),
        **(state.get("context") or {}),
    }

    result = await run_react_agent(
        system_prompt=system_prompt,
        tools=tools,
        user_message=request,
        context=agent_context,
        session_id=session_id,
    )

    return {
        "result": result,
        "messages": [{"role": "assistant", "content": result.get("result", "")}],
    }


async def check_hitl(state: PlumbProState) -> Dict[str, Any]:
    """Check whether the module result requires human-in-the-loop approval.

    For modules in ``_HITL_MODULES`` (estimates, permits, communication),
    the graph will have been interrupted *before* this node executes.
    When the gateway resumes the graph after user approval, this node
    marks the pipeline as complete.

    For non-HITL modules the node simply marks the pipeline as complete.
    """
    module_name = state["module"]
    session_id = state["session_id"]
    result = state.get("result") or {}

    # If the module had an error, propagate it
    if result.get("status") == "error":
        return {"status": "error"}

    if module_name in _HITL_MODULES:
        logger.info(
            "[Router] module '%s' requires HITL approval — interrupting",
            module_name,
        )
        if session_id:
            await emit_agent_event(session_id, "hitl_pending", {
                "module": module_name,
                "result_preview": (result.get("result") or "")[:500],
            })

        # Interrupt and wait for human approval.  The gateway will resume
        # the graph with an approval signal.  When we resume we fall
        # through to the return below.
        approval = interrupt(
            {
                "type": "approval_required",
                "module": module_name,
                "preview": (result.get("result") or "")[:1000],
            }
        )

        logger.info("[Router] HITL approval received: %s", approval)

        if session_id:
            await emit_agent_event(session_id, "hitl_approved", {
                "module": module_name,
                "approval": approval,
            })

    return {"status": "complete"}


# -----------------------------------------------------------------------
# Graph construction
# -----------------------------------------------------------------------


def build_router(checkpointer: Any = None) -> Any:
    """Build and compile the PlumbPro orchestrator graph.

    Returns a compiled LangGraph ``StateGraph`` ready to be invoked or
    streamed.
    """
    graph = StateGraph(PlumbProState)

    # Add nodes
    graph.add_node("classify_request", classify_request)
    graph.add_node("run_module", run_module)
    graph.add_node("check_hitl", check_hitl)

    # Add edges
    graph.add_edge(START, "classify_request")
    graph.add_edge("classify_request", "run_module")
    graph.add_edge("run_module", "check_hitl")
    graph.add_edge("check_hitl", END)

    # Compile with HITL interrupt support
    compile_kwargs: dict[str, Any] = {"interrupt_before": ["check_hitl"]}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
    compiled = graph.compile(**compile_kwargs)

    logger.info("[Router] graph compiled with HITL interrupt support")
    return compiled
