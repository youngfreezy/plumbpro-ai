"""Authentication and team management routes.

Handles:
  - POST /api/auth/register  -- Create company + owner user
  - POST /api/auth/login     -- Verify password, return user data
  - GET  /api/auth/me        -- Return current user from JWT
  - POST /api/company/invite -- Invite team member (owner/admin only)
  - GET  /api/company/team   -- List team members for user's company
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import bcrypt
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from backend.shared.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    company_name: str
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class InviteRequest(BaseModel):
    email: EmailStr
    name: str
    role: str = "technician"  # technician | dispatcher | admin


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _row_to_dict(row, description) -> Optional[dict]:
    """Convert a psycopg row + cursor.description to a dict."""
    if row is None:
        return None
    cols = [col.name for col in description]
    return dict(zip(cols, row))


def _sanitize_user(user: dict) -> dict:
    """Strip sensitive fields before returning user data to the client."""
    safe = {k: v for k, v in user.items() if k != "password_hash"}
    # Ensure id fields are strings for JSON serialization
    for key in ("id", "company_id"):
        if key in safe and safe[key] is not None:
            safe[key] = str(safe[key])
    # Serialize datetimes
    for key in ("created_at", "updated_at"):
        if key in safe and isinstance(safe[key], datetime):
            safe[key] = safe[key].isoformat()
    return safe


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@router.post("/api/auth/register")
async def register(body: RegisterRequest):
    """Create a new company and its owner user account."""
    company_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    password_hash = _hash_password(body.password)

    with get_connection() as conn:
        # Check if email already exists
        cur = conn.execute(
            "SELECT id FROM users WHERE email = %s",
            (body.email,),
        )
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Email already registered")

        # Create company
        conn.execute(
            """INSERT INTO companies (id, name, created_at, updated_at)
               VALUES (%s, %s, %s, %s)""",
            (company_id, body.company_name, now, now),
        )

        # Create owner user
        conn.execute(
            """INSERT INTO users (id, company_id, email, password_hash, name, role, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, company_id, body.email, password_hash, body.name, "owner", now, now),
        )
        conn.commit()

    logger.info("Registered company %s (%s) with owner %s", company_id, body.company_name, body.email)

    return {
        "company": {
            "id": company_id,
            "name": body.company_name,
        },
        "user": {
            "id": user_id,
            "email": body.email,
            "name": body.name,
            "role": "owner",
            "company_id": company_id,
        },
    }


@router.post("/api/auth/login")
async def login(body: LoginRequest):
    """Verify credentials and return user data.

    The frontend (NextAuth) handles JWT creation; this just validates
    the email+password and returns the user profile.
    """
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM users WHERE email = %s",
            (body.email,),
        )
        row = cur.fetchone()
        user = _row_to_dict(row, cur.description)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not _verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    logger.info("Login successful for %s", body.email)
    return {"user": _sanitize_user(user)}


@router.get("/api/auth/me")
async def me(request: Request):
    """Return the current user resolved from JWT authentication."""
    email = getattr(request.state, "user_email", None)
    if not email:
        raise HTTPException(status_code=401, detail="Authentication required")

    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        user = _row_to_dict(row, cur.description)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Also fetch company name
    company_name = None
    with get_connection() as conn:
        cur = conn.execute("SELECT name FROM companies WHERE id = %s", (user["company_id"],))
        company_row = cur.fetchone()
        if company_row:
            company_name = company_row[0]

    safe_user = _sanitize_user(user)
    safe_user["company_name"] = company_name
    return {"user": safe_user}


# ---------------------------------------------------------------------------
# Company / team management routes
# ---------------------------------------------------------------------------

@router.post("/api/company/invite")
async def invite_team_member(body: InviteRequest, request: Request):
    """Invite a new team member to the company.

    Creates the user record with a temporary password. In production,
    this would send an invite email with a password-reset link.
    Requires the requesting user to be an owner or admin.
    """
    email = getattr(request.state, "user_email", None)
    company_id = getattr(request.state, "company_id", None)
    if not email or not company_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Verify requester is owner or admin
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT role FROM users WHERE email = %s AND company_id = %s",
            (email, company_id),
        )
        row = cur.fetchone()

    if not row or row[0] not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owners and admins can invite team members")

    # Validate role
    if body.role not in ("technician", "dispatcher", "admin"):
        raise HTTPException(status_code=400, detail="Role must be technician, dispatcher, or admin")

    # Check if invitee email already exists
    with get_connection() as conn:
        cur = conn.execute("SELECT id FROM users WHERE email = %s", (body.email,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Email already registered")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    # Generate a temporary password -- in production, send an invite email instead
    temp_password = str(uuid.uuid4())[:12]
    password_hash = _hash_password(temp_password)

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO users (id, company_id, email, password_hash, name, role, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, company_id, body.email, password_hash, body.name, body.role, now, now),
        )
        conn.commit()

    logger.info(
        "Invited %s (%s) to company %s as %s by %s",
        body.email, body.name, company_id, body.role, email,
    )

    # TODO: Send invite email with password reset link via Resend
    # from backend.shared.email import send_invite_email
    # await send_invite_email(body.email, body.name, company_name, temp_password)

    return {
        "user": {
            "id": user_id,
            "email": body.email,
            "name": body.name,
            "role": body.role,
            "company_id": company_id,
        },
        "message": "Team member invited. They will receive an email to set their password.",
    }


@router.get("/api/company/team")
async def list_team(request: Request):
    """List all team members for the current user's company."""
    email = getattr(request.state, "user_email", None)
    company_id = getattr(request.state, "company_id", None)
    if not email or not company_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    with get_connection() as conn:
        cur = conn.execute(
            """SELECT id, email, name, role, created_at, updated_at
               FROM users
               WHERE company_id = %s
               ORDER BY created_at ASC""",
            (company_id,),
        )
        rows = cur.fetchall()
        cols = [col.name for col in cur.description]

    team = []
    for row in rows:
        member = dict(zip(cols, row))
        member["id"] = str(member["id"])
        for key in ("created_at", "updated_at"):
            if key in member and isinstance(member[key], datetime):
                member[key] = member[key].isoformat()
        team.append(member)

    return {"team": team}
