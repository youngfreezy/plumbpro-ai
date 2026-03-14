"""Persistent storage for users (team members).

Follows the JHA store pattern: sync psycopg with connection pool,
_row_to_dict helper with cur.description. Includes bcrypt password hashing.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import bcrypt

from backend.shared.db import get_connection

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'technician',
    phone TEXT,
    password_hash TEXT,
    avatar_url TEXT,
    certifications JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_company ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
"""


def _connect():
    return get_connection()


def _hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


async def ensure_users_table() -> None:
    """Create the users table if it doesn't exist."""
    def _create():
        with _connect() as conn:
            conn.execute(_CREATE_TABLE)
            conn.commit()

    await asyncio.to_thread(_create)
    logger.info("users table ensured")


async def create_user(
    company_id: str,
    email: str,
    name: str,
    role: str = "technician",
    password_hash: Optional[str] = None,
    *,
    password: Optional[str] = None,
    phone: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert a new user and return its row as a dict.

    If ``password`` is provided (plaintext), it will be bcrypt-hashed.
    If ``password_hash`` is provided directly, it is stored as-is.
    """
    user_id = str(uuid.uuid4())
    final_hash = password_hash
    if password and not final_hash:
        final_hash = _hash_password(password)

    def _insert():
        with _connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO users (id, company_id, email, name, role, password_hash, phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (user_id, company_id, email, name, role, final_hash, phone),
            )
            row = cur.fetchone()
            conn.commit()
            return _row_to_dict(row, cur.description)

    return await asyncio.to_thread(_insert)


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Fetch a user by email address."""
    def _get():
        with _connect() as conn:
            cur = conn.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,),
            )
            row = cur.fetchone()
            return _row_to_dict(row, cur.description) if row else None

    return await asyncio.to_thread(_get)


async def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a user by ID."""
    def _get():
        with _connect() as conn:
            cur = conn.execute(
                "SELECT * FROM users WHERE id = %s",
                (user_id,),
            )
            row = cur.fetchone()
            return _row_to_dict(row, cur.description) if row else None

    return await asyncio.to_thread(_get)


async def get_team_members(company_id: str) -> List[Dict[str, Any]]:
    """Return all users belonging to a company, ordered by name."""
    def _list():
        with _connect() as conn:
            cur = conn.execute(
                """
                SELECT * FROM users
                WHERE company_id = %s AND is_active = TRUE
                ORDER BY name ASC
                """,
                (company_id,),
            )
            return [_row_to_dict(r, cur.description) for r in cur.fetchall()]

    return await asyncio.to_thread(_list)


async def update_user_role(user_id: str, role: str) -> Optional[Dict[str, Any]]:
    """Update a user's role."""
    def _update():
        with _connect() as conn:
            cur = conn.execute(
                """
                UPDATE users
                SET role = %s, updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                (role, user_id),
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
    # Never expose password hash in serialized output
    result.pop("password_hash", None)
    return result
