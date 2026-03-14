"""Persistent storage for jobs (service calls / work orders).

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
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    assigned_technician_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'other',
    priority TEXT DEFAULT 'normal',
    status TEXT DEFAULT 'pending',
    scheduled_start TIMESTAMPTZ,
    scheduled_end TIMESTAMPTZ,
    actual_start TIMESTAMPTZ,
    actual_end TIMESTAMPTZ,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    estimate_id UUID,
    photos JSONB DEFAULT '[]',
    notes TEXT,
    internal_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(company_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_technician ON jobs(assigned_technician_id);
CREATE INDEX IF NOT EXISTS idx_jobs_customer ON jobs(customer_id);
CREATE INDEX IF NOT EXISTS idx_jobs_scheduled ON jobs(scheduled_start);
"""


def _connect():
    return get_connection()


async def ensure_jobs_table() -> None:
    """Create the jobs table if it doesn't exist."""
    def _create():
        with _connect() as conn:
            conn.execute(_CREATE_TABLE)
            conn.commit()

    await asyncio.to_thread(_create)
    logger.info("jobs table ensured")


async def create_job(company_id: str, data_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new job and return its row as a dict.

    ``data_dict`` should contain keys matching column names (title, description,
    category, priority, customer_id, assigned_technician_id, address, etc.).
    """
    job_id = str(uuid.uuid4())

    # Extract fields with defaults
    title = data_dict.get("title", "Untitled Job")
    description = data_dict.get("description")
    category = data_dict.get("category", "other")
    priority = data_dict.get("priority", "normal")
    status = data_dict.get("status", "pending")
    customer_id = data_dict.get("customer_id")
    assigned_technician_id = data_dict.get("assigned_technician_id")
    scheduled_start = data_dict.get("scheduled_start")
    scheduled_end = data_dict.get("scheduled_end")
    address = data_dict.get("address")
    city = data_dict.get("city")
    state = data_dict.get("state")
    zip_code = data_dict.get("zip_code")
    lat = data_dict.get("lat")
    lng = data_dict.get("lng")
    notes = data_dict.get("notes")
    internal_notes = data_dict.get("internal_notes")
    photos = data_dict.get("photos", [])

    def _insert():
        with _connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO jobs (
                    id, company_id, customer_id, assigned_technician_id,
                    title, description, category, priority, status,
                    scheduled_start, scheduled_end,
                    address, city, state, zip_code, lat, lng,
                    notes, internal_notes, photos
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
                RETURNING *
                """,
                (
                    job_id, company_id, customer_id, assigned_technician_id,
                    title, description, category, priority, status,
                    scheduled_start, scheduled_end,
                    address, city, state, zip_code, lat, lng,
                    notes, internal_notes, json.dumps(photos),
                ),
            )
            row = cur.fetchone()
            conn.commit()
            return _row_to_dict(row, cur.description)

    return await asyncio.to_thread(_insert)


async def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a job by ID."""
    def _get():
        with _connect() as conn:
            cur = conn.execute(
                "SELECT * FROM jobs WHERE id = %s",
                (job_id,),
            )
            row = cur.fetchone()
            return _row_to_dict(row, cur.description) if row else None

    return await asyncio.to_thread(_get)


async def list_jobs(
    company_id: str,
    filters_dict: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """List jobs for a company with optional filters.

    Supported filter keys: status, priority, category, assigned_technician_id,
    customer_id, from_date, to_date (applied to scheduled_start).
    """
    filters = filters_dict or {}
    clauses = ["company_id = %s"]
    params: list[Any] = [company_id]

    if "status" in filters:
        clauses.append("status = %s")
        params.append(filters["status"])
    if "priority" in filters:
        clauses.append("priority = %s")
        params.append(filters["priority"])
    if "category" in filters:
        clauses.append("category = %s")
        params.append(filters["category"])
    if "assigned_technician_id" in filters:
        clauses.append("assigned_technician_id = %s")
        params.append(filters["assigned_technician_id"])
    if "customer_id" in filters:
        clauses.append("customer_id = %s")
        params.append(filters["customer_id"])
    if "from_date" in filters:
        clauses.append("scheduled_start >= %s")
        params.append(filters["from_date"])
    if "to_date" in filters:
        clauses.append("scheduled_start <= %s")
        params.append(filters["to_date"])

    where = " AND ".join(clauses)

    def _list():
        with _connect() as conn:
            cur = conn.execute(
                f"SELECT * FROM jobs WHERE {where} ORDER BY scheduled_start ASC NULLS LAST, created_at DESC",
                params,
            )
            return [_row_to_dict(r, cur.description) for r in cur.fetchall()]

    return await asyncio.to_thread(_list)


async def update_job_status(job_id: str, status: str) -> Optional[Dict[str, Any]]:
    """Update a job's status. Automatically sets actual_start/actual_end timestamps."""
    def _update():
        with _connect() as conn:
            # Set actual_start when moving to in_progress
            extra_set = ""
            if status == "in_progress":
                extra_set = ", actual_start = COALESCE(actual_start, NOW())"
            elif status in ("completed", "cancelled"):
                extra_set = ", actual_end = NOW()"

            cur = conn.execute(
                f"""
                UPDATE jobs
                SET status = %s, updated_at = NOW(){extra_set}
                WHERE id = %s
                RETURNING *
                """,
                (status, job_id),
            )
            row = cur.fetchone()
            conn.commit()
            return _row_to_dict(row, cur.description) if row else None

    return await asyncio.to_thread(_update)


async def update_job(job_id: str, data_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update arbitrary fields on a job."""
    allowed = {
        "title", "description", "category", "priority", "status",
        "customer_id", "assigned_technician_id",
        "scheduled_start", "scheduled_end", "actual_start", "actual_end",
        "address", "city", "state", "zip_code", "lat", "lng",
        "estimate_id", "notes", "internal_notes", "photos",
    }
    filtered = {k: v for k, v in data_dict.items() if k in allowed}
    if not filtered:
        return await get_job(job_id)

    # JSON-encode JSONB fields
    if "photos" in filtered and not isinstance(filtered["photos"], str):
        filtered["photos"] = json.dumps(filtered["photos"])

    filtered["updated_at"] = datetime.now()

    set_clauses = ", ".join(f"{k} = %s" for k in filtered)
    values = list(filtered.values())

    def _update():
        with _connect() as conn:
            cur = conn.execute(
                f"UPDATE jobs SET {set_clauses} WHERE id = %s RETURNING *",
                values + [job_id],
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
