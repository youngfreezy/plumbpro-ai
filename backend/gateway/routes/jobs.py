"""Job / work order routes.

Handles:
  - GET    /api/jobs              -- List jobs for company
  - POST   /api/jobs              -- Create job
  - GET    /api/jobs/{job_id}     -- Get job detail
  - PUT    /api/jobs/{job_id}     -- Update job
  - PATCH  /api/jobs/{job_id}/status -- Update job status
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.shared.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CreateJobRequest(BaseModel):
    customer_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    job_type: str = "service"  # service | installation | inspection | emergency
    priority: str = "normal"   # low | normal | high | emergency
    scheduled_start: Optional[str] = None  # ISO datetime
    scheduled_end: Optional[str] = None
    assigned_technician_id: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    estimated_cost: Optional[float] = None


class UpdateJobRequest(BaseModel):
    customer_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    job_type: Optional[str] = None
    priority: Optional[str] = None
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    assigned_technician_id: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None


class UpdateStatusRequest(BaseModel):
    status: str  # pending | scheduled | in_progress | completed | cancelled | on_hold


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row, description) -> Optional[dict]:
    if row is None:
        return None
    cols = [col.name for col in description]
    return dict(zip(cols, row))


def _serialize_job(job: dict) -> dict:
    """Ensure all fields are JSON-serializable."""
    result = {}
    for k, v in job.items():
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, uuid.UUID):
            result[k] = str(v)
        else:
            result[k] = v
    return result


def _require_auth(request: Request) -> tuple[str, str]:
    """Extract and validate user_email and company_id from request state."""
    email = getattr(request.state, "user_email", None)
    company_id = getattr(request.state, "company_id", None)
    if not email or not company_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return email, company_id


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("")
async def list_jobs(request: Request):
    """List jobs for the user's company with optional filters.

    Query params:
      - status: filter by job status
      - date: filter by scheduled date (YYYY-MM-DD)
      - technician_id: filter by assigned technician
      - customer_id: filter by customer
      - limit: max results (default 50)
      - offset: pagination offset (default 0)
    """
    _email, company_id = _require_auth(request)

    # Build dynamic WHERE clause
    conditions = ["j.company_id = %s"]
    params: list = [company_id]

    status = request.query_params.get("status")
    if status:
        conditions.append("j.status = %s")
        params.append(status)

    date_filter = request.query_params.get("date")
    if date_filter:
        conditions.append("DATE(j.scheduled_start) = %s")
        params.append(date_filter)

    technician_id = request.query_params.get("technician_id")
    if technician_id:
        conditions.append("j.assigned_technician_id = %s")
        params.append(technician_id)

    customer_id = request.query_params.get("customer_id")
    if customer_id:
        conditions.append("j.customer_id = %s")
        params.append(customer_id)

    limit = int(request.query_params.get("limit", "50"))
    offset = int(request.query_params.get("offset", "0"))

    where_clause = " AND ".join(conditions)

    with get_connection() as conn:
        cur = conn.execute(
            f"""SELECT j.*,
                       c.name AS customer_name,
                       u.name AS technician_name
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.id
                LEFT JOIN users u ON j.assigned_technician_id = u.id
                WHERE {where_clause}
                ORDER BY j.scheduled_start DESC NULLS LAST, j.created_at DESC
                LIMIT %s OFFSET %s""",
            (*params, limit, offset),
        )
        rows = cur.fetchall()
        cols = [col.name for col in cur.description]

    jobs = [_serialize_job(dict(zip(cols, row))) for row in rows]

    # Get total count for pagination
    with get_connection() as conn:
        cur = conn.execute(
            f"SELECT COUNT(*) FROM jobs j WHERE {where_clause}",
            tuple(params),
        )
        total = cur.fetchone()[0]

    return {"jobs": jobs, "total": total, "limit": limit, "offset": offset}


@router.post("")
async def create_job(body: CreateJobRequest, request: Request):
    """Create a new job / work order."""
    _email, company_id = _require_auth(request)

    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    with get_connection() as conn:
        # Validate customer belongs to company (if provided)
        if body.customer_id:
            cur = conn.execute(
                "SELECT id FROM customers WHERE id = %s AND company_id = %s",
                (body.customer_id, company_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Customer not found")

        # Validate technician belongs to company (if provided)
        if body.assigned_technician_id:
            cur = conn.execute(
                "SELECT id FROM users WHERE id = %s AND company_id = %s",
                (body.assigned_technician_id, company_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Technician not found")

        cur = conn.execute(
            """INSERT INTO jobs (
                id, company_id, customer_id, title, description, job_type,
                priority, status, scheduled_start, scheduled_end,
                assigned_technician_id, address, notes, estimated_cost,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            ) RETURNING *""",
            (
                job_id, company_id, body.customer_id, body.title, body.description,
                body.job_type, body.priority, "pending",
                body.scheduled_start, body.scheduled_end,
                body.assigned_technician_id, body.address, body.notes,
                body.estimated_cost, now, now,
            ),
        )
        row = cur.fetchone()
        job = _row_to_dict(row, cur.description)
        conn.commit()

    logger.info("Created job %s for company %s", job_id, company_id)
    return {"job": _serialize_job(job)}


@router.get("/{job_id}")
async def get_job(job_id: str, request: Request):
    """Get detailed job information including customer and technician data."""
    _email, company_id = _require_auth(request)

    with get_connection() as conn:
        cur = conn.execute(
            """SELECT j.*,
                      c.name AS customer_name, c.email AS customer_email,
                      c.phone AS customer_phone, c.address AS customer_address,
                      u.name AS technician_name, u.email AS technician_email
               FROM jobs j
               LEFT JOIN customers c ON j.customer_id = c.id
               LEFT JOIN users u ON j.assigned_technician_id = u.id
               WHERE j.id = %s AND j.company_id = %s""",
            (job_id, company_id),
        )
        row = cur.fetchone()
        job = _row_to_dict(row, cur.description)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"job": _serialize_job(job)}


@router.put("/{job_id}")
async def update_job(job_id: str, body: UpdateJobRequest, request: Request):
    """Update job details."""
    _email, company_id = _require_auth(request)

    # Build SET clause dynamically from non-None fields
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates["updated_at"] = datetime.now(timezone.utc)

    set_parts = []
    values = []
    for key, value in updates.items():
        set_parts.append(f"{key} = %s")
        values.append(value)

    set_clause = ", ".join(set_parts)
    values.extend([job_id, company_id])

    with get_connection() as conn:
        # Validate technician if being reassigned
        if body.assigned_technician_id:
            cur = conn.execute(
                "SELECT id FROM users WHERE id = %s AND company_id = %s",
                (body.assigned_technician_id, company_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Technician not found")

        cur = conn.execute(
            f"""UPDATE jobs SET {set_clause}
                WHERE id = %s AND company_id = %s
                RETURNING *""",
            tuple(values),
        )
        row = cur.fetchone()
        job = _row_to_dict(row, cur.description)
        conn.commit()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    logger.info("Updated job %s", job_id)
    return {"job": _serialize_job(job)}


@router.patch("/{job_id}/status")
async def update_job_status(job_id: str, body: UpdateStatusRequest, request: Request):
    """Update the status of a job."""
    _email, company_id = _require_auth(request)

    valid_statuses = {"pending", "scheduled", "in_progress", "completed", "cancelled", "on_hold"}
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}",
        )

    now = datetime.now(timezone.utc)

    with get_connection() as conn:
        # If completing, also set completed_at timestamp
        if body.status == "completed":
            cur = conn.execute(
                """UPDATE jobs SET status = %s, completed_at = %s, updated_at = %s
                   WHERE id = %s AND company_id = %s
                   RETURNING *""",
                (body.status, now, now, job_id, company_id),
            )
        else:
            cur = conn.execute(
                """UPDATE jobs SET status = %s, updated_at = %s
                   WHERE id = %s AND company_id = %s
                   RETURNING *""",
                (body.status, now, job_id, company_id),
            )
        row = cur.fetchone()
        job = _row_to_dict(row, cur.description)
        conn.commit()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    logger.info("Updated job %s status to %s", job_id, body.status)
    return {"job": _serialize_job(job)}
