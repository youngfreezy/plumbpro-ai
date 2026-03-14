"""Persistent storage for agent sessions.

Follows the JHA store pattern: sync psycopg with connection pool,
_row_to_dict helper with cur.description.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from backend.shared.db import get_connection

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    module TEXT NOT NULL,
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    status TEXT DEFAULT 'running',
    state_snapshot JSONB,
    result JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sessions_company ON agent_sessions(company_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON agent_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON agent_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_job ON agent_sessions(job_id);
"""


def _connect():
    return get_connection()


async def ensure_agent_sessions_table() -> None:
    """Create the agent_sessions table if it doesn't exist."""
    def _create():
        with _connect() as conn:
            conn.execute(_CREATE_TABLE)
            conn.commit()

    await asyncio.to_thread(_create)
    logger.info("agent_sessions table ensured")


async def create_session(
    company_id: str,
    user_id: str,
    module: str,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert a new agent session and return its row as a dict."""
    session_id = str(uuid.uuid4())

    def _insert():
        with _connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO agent_sessions (id, company_id, user_id, module, job_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (session_id, company_id, user_id, module, job_id),
            )
            row = cur.fetchone()
            conn.commit()
            return _row_to_dict(row, cur.description)

    return await asyncio.to_thread(_insert)


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a session by ID."""
    def _get():
        with _connect() as conn:
            cur = conn.execute(
                "SELECT * FROM agent_sessions WHERE id = %s",
                (session_id,),
            )
            row = cur.fetchone()
            return _row_to_dict(row, cur.description) if row else None

    return await asyncio.to_thread(_get)


async def update_session_state(
    session_id: str,
    state_snapshot: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Persist the agent's LangGraph state snapshot."""
    def _update():
        with _connect() as conn:
            cur = conn.execute(
                """
                UPDATE agent_sessions
                SET state_snapshot = %s::jsonb, updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                (json.dumps(state_snapshot), session_id),
            )
            row = cur.fetchone()
            conn.commit()
            return _row_to_dict(row, cur.description) if row else None

    return await asyncio.to_thread(_update)


async def update_session_status(
    session_id: str,
    status: str,
    *,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update a session's status and optionally set result or error."""
    def _update():
        with _connect() as conn:
            cur = conn.execute(
                """
                UPDATE agent_sessions
                SET status = %s,
                    result = COALESCE(%s::jsonb, result),
                    error = COALESCE(%s, error),
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                (
                    status,
                    json.dumps(result) if result else None,
                    error,
                    session_id,
                ),
            )
            row = cur.fetchone()
            conn.commit()
            return _row_to_dict(row, cur.description) if row else None

    return await asyncio.to_thread(_update)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row, description) -> Dict[str, Any]:
    if row is None:
        return {}
    cols = [d.name for d in description]
    result = dict(zip(cols, row))
    for k, v in result.items():
        if isinstance(v, uuid.UUID):
            result[k] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, memoryview):
            result[k] = bytes(v)
    return result
