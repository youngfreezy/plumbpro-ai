"""Scheduling and route optimization routes.

Handles:
  - GET  /api/schedule          -- Get schedule for date range
  - POST /api/schedule/optimize -- Trigger route optimization for a day
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

router = APIRouter(prefix="/api/schedule", tags=["scheduling"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class OptimizeRequest(BaseModel):
    date: str  # YYYY-MM-DD
    technician_id: Optional[str] = None  # Optimize for specific tech, or all if None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize(obj: dict) -> dict:
    result = {}
    for k, v in obj.items():
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, uuid.UUID):
            result[k] = str(v)
        else:
            result[k] = v
    return result


def _require_auth(request: Request) -> tuple[str, str]:
    email = getattr(request.state, "user_email", None)
    company_id = getattr(request.state, "company_id", None)
    if not email or not company_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return email, company_id


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("")
async def get_schedule(request: Request):
    """Get schedule for a date range.

    Query params:
      - start_date: YYYY-MM-DD (required)
      - end_date: YYYY-MM-DD (required)
      - technician_id: filter by specific technician (optional)
    """
    _email, company_id = _require_auth(request)

    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")

    if not start_date or not end_date:
        raise HTTPException(status_code=400, detail="start_date and end_date are required")

    conditions = [
        "j.company_id = %s",
        "DATE(j.scheduled_start) >= %s",
        "DATE(j.scheduled_start) <= %s",
        "j.status NOT IN ('cancelled')",
    ]
    params: list = [company_id, start_date, end_date]

    technician_id = request.query_params.get("technician_id")
    if technician_id:
        conditions.append("j.assigned_technician_id = %s")
        params.append(technician_id)

    where_clause = " AND ".join(conditions)

    with get_connection() as conn:
        cur = conn.execute(
            f"""SELECT j.id, j.title, j.status, j.job_type, j.priority,
                       j.scheduled_start, j.scheduled_end, j.address,
                       j.assigned_technician_id,
                       c.name AS customer_name, c.phone AS customer_phone,
                       u.name AS technician_name
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.id
                LEFT JOIN users u ON j.assigned_technician_id = u.id
                WHERE {where_clause}
                ORDER BY j.scheduled_start ASC""",
            tuple(params),
        )
        rows = cur.fetchall()
        cols = [col.name for col in cur.description]

    events = [_serialize(dict(zip(cols, row))) for row in rows]

    # Group by technician for calendar view
    by_technician: dict[str, list] = {}
    unassigned: list = []
    for event in events:
        tech_id = event.get("assigned_technician_id")
        if tech_id:
            tech_name = event.get("technician_name", "Unknown")
            key = f"{tech_id}"
            if key not in by_technician:
                by_technician[key] = {
                    "technician_id": tech_id,
                    "technician_name": tech_name,
                    "jobs": [],
                }
            by_technician[key]["jobs"].append(event)
        else:
            unassigned.append(event)

    # Get list of all technicians in the company for the schedule view
    with get_connection() as conn:
        cur = conn.execute(
            """SELECT id, name, email FROM users
               WHERE company_id = %s AND role IN ('technician', 'owner', 'admin')
               ORDER BY name ASC""",
            (company_id,),
        )
        tech_rows = cur.fetchall()
        tech_cols = [col.name for col in cur.description]

    technicians = [_serialize(dict(zip(tech_cols, row))) for row in tech_rows]

    return {
        "events": events,
        "by_technician": list(by_technician.values()),
        "unassigned": unassigned,
        "technicians": technicians,
        "start_date": start_date,
        "end_date": end_date,
    }


@router.post("/optimize")
async def optimize_routes(body: OptimizeRequest, request: Request):
    """Trigger route optimization for a given day.

    Uses job addresses and scheduled times to suggest an optimal
    ordering that minimizes travel time between locations.
    This is a placeholder that will integrate with Google Maps
    Distance Matrix API for real optimization.
    """
    _email, company_id = _require_auth(request)

    conditions = [
        "j.company_id = %s",
        "DATE(j.scheduled_start) = %s",
        "j.status NOT IN ('cancelled', 'completed')",
        "j.address IS NOT NULL",
    ]
    params: list = [company_id, body.date]

    if body.technician_id:
        conditions.append("j.assigned_technician_id = %s")
        params.append(body.technician_id)

    where_clause = " AND ".join(conditions)

    with get_connection() as conn:
        cur = conn.execute(
            f"""SELECT j.id, j.title, j.address, j.scheduled_start, j.scheduled_end,
                       j.assigned_technician_id, j.priority,
                       u.name AS technician_name
                FROM jobs j
                LEFT JOIN users u ON j.assigned_technician_id = u.id
                WHERE {where_clause}
                ORDER BY j.scheduled_start ASC""",
            tuple(params),
        )
        rows = cur.fetchall()
        cols = [col.name for col in cur.description]

    jobs = [_serialize(dict(zip(cols, row))) for row in rows]

    if not jobs:
        return {
            "optimized": False,
            "message": "No jobs with addresses found for the given date",
            "jobs": [],
        }

    # Group by technician
    tech_jobs: dict[str, list] = {}
    for job in jobs:
        tech_id = job.get("assigned_technician_id", "unassigned")
        if tech_id not in tech_jobs:
            tech_jobs[tech_id] = []
        tech_jobs[tech_id].append(job)

    # Basic optimization: sort by address proximity (naive -- just by priority for now).
    # TODO: Integrate Google Maps Distance Matrix API for real route optimization.
    optimized_routes = []
    for tech_id, tech_job_list in tech_jobs.items():
        # Sort: emergency first, then high, normal, low
        priority_order = {"emergency": 0, "high": 1, "normal": 2, "low": 3}
        sorted_jobs = sorted(
            tech_job_list,
            key=lambda j: (priority_order.get(j.get("priority", "normal"), 2), j.get("scheduled_start", "")),
        )
        optimized_routes.append({
            "technician_id": tech_id,
            "technician_name": sorted_jobs[0].get("technician_name", "Unassigned"),
            "jobs": sorted_jobs,
            "total_stops": len(sorted_jobs),
        })

    logger.info(
        "Route optimization for %s: %d technicians, %d jobs",
        body.date, len(optimized_routes), len(jobs),
    )

    return {
        "optimized": True,
        "date": body.date,
        "routes": optimized_routes,
        "total_jobs": len(jobs),
        "message": "Routes optimized by priority. Full distance-based optimization coming soon.",
    }
