"""Customer CRM routes.

Handles:
  - GET  /api/customers                -- List customers for company
  - POST /api/customers                -- Create customer
  - GET  /api/customers/{customer_id}  -- Get customer with job history
  - PUT  /api/customers/{customer_id}  -- Update customer
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

from backend.shared.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/customers", tags=["customers"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CreateCustomerRequest(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    notes: Optional[str] = None


class UpdateCustomerRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row, description) -> Optional[dict]:
    if row is None:
        return None
    cols = [col.name for col in description]
    return dict(zip(cols, row))


def _serialize(obj: dict) -> dict:
    """Ensure all fields are JSON-serializable."""
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
async def list_customers(request: Request):
    """List all customers for the user's company.

    Query params:
      - search: search by name, email, or phone
      - limit: max results (default 50)
      - offset: pagination offset (default 0)
    """
    _email, company_id = _require_auth(request)

    conditions = ["company_id = %s"]
    params: list = [company_id]

    search = request.query_params.get("search")
    if search:
        conditions.append(
            "(name ILIKE %s OR email ILIKE %s OR phone ILIKE %s)"
        )
        like_pattern = f"%{search}%"
        params.extend([like_pattern, like_pattern, like_pattern])

    limit = int(request.query_params.get("limit", "50"))
    offset = int(request.query_params.get("offset", "0"))

    where_clause = " AND ".join(conditions)

    with get_connection() as conn:
        cur = conn.execute(
            f"""SELECT * FROM customers
                WHERE {where_clause}
                ORDER BY name ASC
                LIMIT %s OFFSET %s""",
            (*params, limit, offset),
        )
        rows = cur.fetchall()
        cols = [col.name for col in cur.description]

    customers = [_serialize(dict(zip(cols, row))) for row in rows]

    # Total count
    with get_connection() as conn:
        cur = conn.execute(
            f"SELECT COUNT(*) FROM customers WHERE {where_clause}",
            tuple(params),
        )
        total = cur.fetchone()[0]

    return {"customers": customers, "total": total, "limit": limit, "offset": offset}


@router.post("")
async def create_customer(body: CreateCustomerRequest, request: Request):
    """Create a new customer record."""
    _email, company_id = _require_auth(request)

    customer_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    with get_connection() as conn:
        # Check for duplicate email within the company
        if body.email:
            cur = conn.execute(
                "SELECT id FROM customers WHERE email = %s AND company_id = %s",
                (body.email, company_id),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="Customer with this email already exists")

        cur = conn.execute(
            """INSERT INTO customers (
                id, company_id, name, email, phone, address,
                city, state, zip_code, notes, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *""",
            (
                customer_id, company_id, body.name, body.email, body.phone,
                body.address, body.city, body.state, body.zip_code,
                body.notes, now, now,
            ),
        )
        row = cur.fetchone()
        customer = _row_to_dict(row, cur.description)
        conn.commit()

    logger.info("Created customer %s for company %s", customer_id, company_id)
    return {"customer": _serialize(customer)}


@router.get("/{customer_id}")
async def get_customer(customer_id: str, request: Request):
    """Get customer details including their job history."""
    _email, company_id = _require_auth(request)

    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM customers WHERE id = %s AND company_id = %s",
            (customer_id, company_id),
        )
        row = cur.fetchone()
        customer = _row_to_dict(row, cur.description)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Fetch job history for this customer
    with get_connection() as conn:
        cur = conn.execute(
            """SELECT j.id, j.title, j.status, j.job_type, j.priority,
                      j.scheduled_start, j.completed_at, j.actual_cost,
                      u.name AS technician_name
               FROM jobs j
               LEFT JOIN users u ON j.assigned_technician_id = u.id
               WHERE j.customer_id = %s AND j.company_id = %s
               ORDER BY j.created_at DESC
               LIMIT 50""",
            (customer_id, company_id),
        )
        job_rows = cur.fetchall()
        job_cols = [col.name for col in cur.description]

    jobs = [_serialize(dict(zip(job_cols, row))) for row in job_rows]

    result = _serialize(customer)
    result["jobs"] = jobs
    result["total_jobs"] = len(jobs)

    return {"customer": result}


@router.put("/{customer_id}")
async def update_customer(customer_id: str, body: UpdateCustomerRequest, request: Request):
    """Update customer details."""
    _email, company_id = _require_auth(request)

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
    values.extend([customer_id, company_id])

    with get_connection() as conn:
        cur = conn.execute(
            f"""UPDATE customers SET {set_clause}
                WHERE id = %s AND company_id = %s
                RETURNING *""",
            tuple(values),
        )
        row = cur.fetchone()
        customer = _row_to_dict(row, cur.description)
        conn.commit()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    logger.info("Updated customer %s", customer_id)
    return {"customer": _serialize(customer)}
