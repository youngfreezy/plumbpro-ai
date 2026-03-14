"""Persistent storage for customers.

Follows the JHA store pattern: sync psycopg with connection pool,
_row_to_dict helper with cur.description.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.shared.db import get_connection

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    notes TEXT,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_customers_company ON customers(company_id);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(company_id, email);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(company_id, phone);
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(company_id, name);
"""


def _connect():
    return get_connection()


async def ensure_customers_table() -> None:
    """Create the customers table if it doesn't exist."""
    def _create():
        with _connect() as conn:
            conn.execute(_CREATE_TABLE)
            conn.commit()

    await asyncio.to_thread(_create)
    logger.info("customers table ensured")


async def create_customer(
    company_id: str,
    data_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """Insert a new customer and return its row as a dict."""
    customer_id = str(uuid.uuid4())

    name = data_dict.get("name", "")
    email = data_dict.get("email")
    phone = data_dict.get("phone")
    address = data_dict.get("address")
    city = data_dict.get("city")
    state = data_dict.get("state")
    zip_code = data_dict.get("zip_code")
    lat = data_dict.get("lat")
    lng = data_dict.get("lng")
    notes = data_dict.get("notes")
    tags = data_dict.get("tags", [])

    def _insert():
        with _connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO customers (
                    id, company_id, name, email, phone,
                    address, city, state, zip_code, lat, lng,
                    notes, tags
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    customer_id, company_id, name, email, phone,
                    address, city, state, zip_code, lat, lng,
                    notes, json.dumps(tags),
                ),
            )
            row = cur.fetchone()
            conn.commit()
            return _row_to_dict(row, cur.description)

    return await asyncio.to_thread(_insert)


async def get_customer(customer_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a customer by ID."""
    def _get():
        with _connect() as conn:
            cur = conn.execute(
                "SELECT * FROM customers WHERE id = %s",
                (customer_id,),
            )
            row = cur.fetchone()
            return _row_to_dict(row, cur.description) if row else None

    return await asyncio.to_thread(_get)


async def list_customers(company_id: str) -> List[Dict[str, Any]]:
    """Return all customers for a company, ordered by name."""
    def _list():
        with _connect() as conn:
            cur = conn.execute(
                "SELECT * FROM customers WHERE company_id = %s ORDER BY name ASC",
                (company_id,),
            )
            return [_row_to_dict(r, cur.description) for r in cur.fetchall()]

    return await asyncio.to_thread(_list)


async def search_customers(
    company_id: str,
    query: str,
) -> List[Dict[str, Any]]:
    """Search customers by name, email, phone, or address (case-insensitive ILIKE)."""
    pattern = f"%{query}%"

    def _search():
        with _connect() as conn:
            cur = conn.execute(
                """
                SELECT * FROM customers
                WHERE company_id = %s
                  AND (
                      name ILIKE %s
                      OR email ILIKE %s
                      OR phone ILIKE %s
                      OR address ILIKE %s
                  )
                ORDER BY name ASC
                LIMIT 50
                """,
                (company_id, pattern, pattern, pattern, pattern),
            )
            return [_row_to_dict(r, cur.description) for r in cur.fetchall()]

    return await asyncio.to_thread(_search)


async def get_customer_by_address(
    company_id: str,
    address: str,
) -> Optional[Dict[str, Any]]:
    """Find a customer by exact address match within a company."""
    def _get():
        with _connect() as conn:
            cur = conn.execute(
                "SELECT * FROM customers WHERE company_id = %s AND address = %s",
                (company_id, address),
            )
            row = cur.fetchone()
            return _row_to_dict(row, cur.description) if row else None

    return await asyncio.to_thread(_get)


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
