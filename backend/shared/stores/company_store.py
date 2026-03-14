"""Persistent storage for companies (tenants).

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
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    owner_email TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    logo_url TEXT,
    settings JSONB DEFAULT '{}',
    stripe_customer_id TEXT,
    subscription_status TEXT DEFAULT 'trialing',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_companies_slug ON companies(slug);
CREATE INDEX IF NOT EXISTS idx_companies_owner ON companies(owner_email);
"""


def _connect():
    return get_connection()


async def ensure_companies_table() -> None:
    """Create the companies table if it doesn't exist."""
    def _create():
        with _connect() as conn:
            conn.execute(_CREATE_TABLE)
            conn.commit()

    await asyncio.to_thread(_create)
    logger.info("companies table ensured")


async def create_company(
    name: str,
    slug: str,
    owner_email: str,
) -> Dict[str, Any]:
    """Insert a new company and return its row as a dict."""
    company_id = str(uuid.uuid4())

    def _insert():
        with _connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO companies (id, name, slug, owner_email)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (company_id, name, slug, owner_email),
            )
            row = cur.fetchone()
            conn.commit()
            return _row_to_dict(row, cur.description)

    return await asyncio.to_thread(_insert)


async def get_company(company_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a company by ID."""
    def _get():
        with _connect() as conn:
            cur = conn.execute(
                "SELECT * FROM companies WHERE id = %s",
                (company_id,),
            )
            row = cur.fetchone()
            return _row_to_dict(row, cur.description) if row else None

    return await asyncio.to_thread(_get)


async def get_company_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Fetch a company by slug."""
    def _get():
        with _connect() as conn:
            cur = conn.execute(
                "SELECT * FROM companies WHERE slug = %s",
                (slug,),
            )
            row = cur.fetchone()
            return _row_to_dict(row, cur.description) if row else None

    return await asyncio.to_thread(_get)


async def update_company_settings(
    company_id: str,
    settings_dict: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Merge new settings into the company's settings JSONB column."""
    def _update():
        with _connect() as conn:
            cur = conn.execute(
                """
                UPDATE companies
                SET settings = settings || %s::jsonb,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                (json.dumps(settings_dict), company_id),
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
