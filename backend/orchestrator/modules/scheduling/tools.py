"""Scheduling tools for the PlumbPro scheduling ReAct agent.

Each tool is decorated with ``@tool`` so LangChain can extract the name,
description (from the docstring), and parameter schema automatically.
Claude reads these descriptions to decide when and how to call them.

All tools interact with the database through ``backend.shared.db`` and
return structured dicts that help the agent make informed decisions.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from langchain_core.tools import tool

from backend.shared.db import get_connection

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# Tools
# -----------------------------------------------------------------------


@tool
def create_job(
    company_id: str,
    customer_name: str,
    description: str,
    priority: str,
    category: str,
    address: str,
) -> dict:
    """Create a new plumbing job in the system.

    Use this when a customer calls in with a new service request. The job
    starts in 'unscheduled' status and must be scheduled separately with
    the schedule_job tool.

    Args:
        company_id: The company this job belongs to.
        customer_name: Full name of the customer.
        description: What the job entails (e.g. "Leaking kitchen faucet").
        priority: One of 'emergency', 'high', 'medium', 'low'.
        category: Type of work — e.g. 'repair', 'installation', 'inspection', 'maintenance'.
        address: Service address where the technician will go.

    Returns:
        A dict with the new job's id, status, and details.
    """
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()

    valid_priorities = {"emergency", "high", "medium", "low"}
    if priority not in valid_priorities:
        return {"error": f"Invalid priority '{priority}'. Must be one of: {valid_priorities}"}

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    id, company_id, customer_name, description, priority,
                    category, address, status, created_at, updated_at
                ) VALUES (
                    %(id)s, %(company_id)s, %(customer_name)s, %(description)s,
                    %(priority)s, %(category)s, %(address)s, 'unscheduled',
                    %(now)s, %(now)s
                )
                """,
                {
                    "id": job_id,
                    "company_id": company_id,
                    "customer_name": customer_name,
                    "description": description,
                    "priority": priority,
                    "category": category,
                    "address": address,
                    "now": now,
                },
            )
            conn.commit()

        logger.info("Created job %s for company %s", job_id, company_id)
        return {
            "job_id": job_id,
            "status": "unscheduled",
            "customer_name": customer_name,
            "description": description,
            "priority": priority,
            "category": category,
            "address": address,
            "created_at": now.isoformat(),
        }
    except Exception as exc:
        logger.error("Failed to create job: %s", exc)
        return {"error": f"Failed to create job: {exc}"}


@tool
def list_jobs_for_date(
    company_id: str,
    date: str,
    technician_id: Optional[str] = None,
) -> list:
    """List all scheduled jobs for a given date, optionally filtered by technician.

    Use this to see what's on the schedule for a particular day, or to
    understand how busy a specific technician is.

    Args:
        company_id: The company to look up jobs for.
        date: The date to list jobs for, in YYYY-MM-DD format.
        technician_id: Optionally filter to only one technician's jobs.

    Returns:
        A list of job dicts with id, customer_name, description, start_time,
        duration_minutes, technician_id, status, and address.
    """
    try:
        # Validate date format
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return [{"error": f"Invalid date format '{date}'. Use YYYY-MM-DD."}]

    try:
        with get_connection() as conn:
            query = """
                SELECT
                    j.id, j.customer_name, j.description, j.priority,
                    j.category, j.address, j.status,
                    s.technician_id, s.start_time, s.duration_minutes
                FROM jobs j
                LEFT JOIN job_schedules s ON j.id = s.job_id
                WHERE j.company_id = %(company_id)s
                  AND s.start_time::date = %(date)s
            """
            params: dict = {"company_id": company_id, "date": target_date}

            if technician_id:
                query += " AND s.technician_id = %(technician_id)s"
                params["technician_id"] = technician_id

            query += " ORDER BY s.start_time ASC"

            cur = conn.execute(query, params)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]

        jobs = []
        for row in rows:
            job = dict(zip(columns, row))
            # Serialize datetime fields
            if job.get("start_time"):
                job["start_time"] = job["start_time"].isoformat()
            jobs.append(job)

        logger.info(
            "Found %d jobs for company %s on %s", len(jobs), company_id, date
        )
        return jobs

    except Exception as exc:
        logger.error("Failed to list jobs: %s", exc)
        return [{"error": f"Failed to list jobs: {exc}"}]


@tool
def check_technician_availability(
    company_id: str,
    technician_id: str,
    date: str,
    start_time: str,
    duration_minutes: int,
) -> dict:
    """Check whether a technician is available for a given time slot.

    ALWAYS call this before scheduling a job to avoid double-booking.

    Args:
        company_id: The company the technician belongs to.
        technician_id: The technician's unique ID.
        date: The date to check, in YYYY-MM-DD format.
        start_time: Proposed start time in HH:MM (24-hour) format.
        duration_minutes: How long the job is expected to take.

    Returns:
        A dict with 'available' (bool), and if not available, 'conflicts'
        listing the overlapping jobs.
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
    except ValueError as exc:
        return {"error": f"Invalid date/time format: {exc}. Use YYYY-MM-DD and HH:MM."}

    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                SELECT
                    s.job_id, j.customer_name, j.description,
                    s.start_time, s.duration_minutes
                FROM job_schedules s
                JOIN jobs j ON s.job_id = j.id
                WHERE s.technician_id = %(technician_id)s
                  AND j.company_id = %(company_id)s
                  AND s.start_time::date = %(date)s
                  AND s.start_time < %(end_dt)s
                  AND (s.start_time + (s.duration_minutes || ' minutes')::interval) > %(start_dt)s
                ORDER BY s.start_time ASC
                """,
                {
                    "technician_id": technician_id,
                    "company_id": company_id,
                    "date": target_date,
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                },
            )
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]

        if not rows:
            return {
                "available": True,
                "technician_id": technician_id,
                "date": date,
                "start_time": start_time,
                "duration_minutes": duration_minutes,
            }

        conflicts = []
        for row in rows:
            conflict = dict(zip(columns, row))
            if conflict.get("start_time"):
                conflict["start_time"] = conflict["start_time"].isoformat()
            conflicts.append(conflict)

        return {
            "available": False,
            "technician_id": technician_id,
            "date": date,
            "start_time": start_time,
            "duration_minutes": duration_minutes,
            "conflicts": conflicts,
        }

    except Exception as exc:
        logger.error("Failed to check availability: %s", exc)
        return {"error": f"Failed to check availability: {exc}"}


@tool
def schedule_job(
    job_id: str,
    technician_id: str,
    start_time: str,
    duration_minutes: int,
) -> dict:
    """Schedule a job by assigning it to a technician at a specific time.

    You should ALWAYS call check_technician_availability first to make sure
    the time slot is open. This tool does not do a conflict check itself.

    Args:
        job_id: The ID of the job to schedule (from create_job).
        technician_id: The technician to assign the job to.
        start_time: When the job starts, in ISO format (YYYY-MM-DDTHH:MM:SS).
        duration_minutes: Expected duration in minutes.

    Returns:
        A dict confirming the schedule was created, with the schedule_id.
    """
    schedule_id = str(uuid.uuid4())
    now = datetime.utcnow()

    try:
        start_dt = datetime.fromisoformat(start_time)
    except ValueError:
        return {"error": f"Invalid start_time format '{start_time}'. Use ISO format YYYY-MM-DDTHH:MM:SS."}

    try:
        with get_connection() as conn:
            # Create the schedule entry
            conn.execute(
                """
                INSERT INTO job_schedules (
                    id, job_id, technician_id, start_time,
                    duration_minutes, created_at
                ) VALUES (
                    %(id)s, %(job_id)s, %(technician_id)s, %(start_time)s,
                    %(duration_minutes)s, %(now)s
                )
                """,
                {
                    "id": schedule_id,
                    "job_id": job_id,
                    "technician_id": technician_id,
                    "start_time": start_dt,
                    "duration_minutes": duration_minutes,
                    "now": now,
                },
            )

            # Update job status to scheduled
            conn.execute(
                """
                UPDATE jobs
                SET status = 'scheduled', updated_at = %(now)s
                WHERE id = %(job_id)s
                """,
                {"job_id": job_id, "now": now},
            )

            conn.commit()

        end_dt = start_dt + timedelta(minutes=duration_minutes)
        logger.info(
            "Scheduled job %s with technician %s at %s",
            job_id, technician_id, start_time,
        )
        return {
            "schedule_id": schedule_id,
            "job_id": job_id,
            "technician_id": technician_id,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "duration_minutes": duration_minutes,
            "status": "scheduled",
        }

    except Exception as exc:
        logger.error("Failed to schedule job: %s", exc)
        return {"error": f"Failed to schedule job: {exc}"}


@tool
def reschedule_job(job_id: str, new_start_time: str) -> dict:
    """Reschedule an existing job to a new time.

    The duration and assigned technician stay the same. Use this when a
    customer needs to move their appointment.

    Args:
        job_id: The ID of the job to reschedule.
        new_start_time: The new start time in ISO format (YYYY-MM-DDTHH:MM:SS).

    Returns:
        A dict confirming the reschedule, with old and new times.
    """
    try:
        new_dt = datetime.fromisoformat(new_start_time)
    except ValueError:
        return {"error": f"Invalid time format '{new_start_time}'. Use ISO format YYYY-MM-DDTHH:MM:SS."}

    now = datetime.utcnow()

    try:
        with get_connection() as conn:
            # Get the current schedule
            cur = conn.execute(
                """
                SELECT id, start_time, duration_minutes, technician_id
                FROM job_schedules
                WHERE job_id = %(job_id)s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                {"job_id": job_id},
            )
            row = cur.fetchone()

            if row is None:
                return {"error": f"No schedule found for job '{job_id}'. Is it scheduled?"}

            columns = [desc[0] for desc in cur.description]
            schedule = dict(zip(columns, row))
            old_start = schedule["start_time"]

            # Update the schedule
            conn.execute(
                """
                UPDATE job_schedules
                SET start_time = %(new_start)s
                WHERE id = %(schedule_id)s
                """,
                {"new_start": new_dt, "schedule_id": schedule["id"]},
            )

            # Touch the job updated_at
            conn.execute(
                """
                UPDATE jobs SET updated_at = %(now)s WHERE id = %(job_id)s
                """,
                {"now": now, "job_id": job_id},
            )

            conn.commit()

        logger.info("Rescheduled job %s from %s to %s", job_id, old_start, new_start_time)
        return {
            "job_id": job_id,
            "old_start_time": old_start.isoformat() if hasattr(old_start, "isoformat") else str(old_start),
            "new_start_time": new_dt.isoformat(),
            "technician_id": schedule["technician_id"],
            "duration_minutes": schedule["duration_minutes"],
            "status": "rescheduled",
        }

    except Exception as exc:
        logger.error("Failed to reschedule job: %s", exc)
        return {"error": f"Failed to reschedule job: {exc}"}


@tool
def get_team_members(company_id: str) -> list:
    """List all technicians (team members) for a company.

    Use this to find out who is available to assign jobs to. Returns each
    technician's ID, name, specialties, and active status.

    Args:
        company_id: The company to list technicians for.

    Returns:
        A list of technician dicts with id, name, phone, email,
        specialties, and is_active.
    """
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                SELECT
                    id, name, phone, email, specialties, is_active
                FROM technicians
                WHERE company_id = %(company_id)s
                  AND is_active = true
                ORDER BY name ASC
                """,
                {"company_id": company_id},
            )
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]

        technicians = [dict(zip(columns, row)) for row in rows]
        logger.info(
            "Found %d active technicians for company %s",
            len(technicians), company_id,
        )
        return technicians

    except Exception as exc:
        logger.error("Failed to list team members: %s", exc)
        return [{"error": f"Failed to list team members: {exc}"}]


@tool
def send_customer_notification(
    customer_id: str,
    message: str,
    channel: str = "sms",
) -> dict:
    """Send a notification to a customer via SMS or email.

    Use this to confirm appointments, send reminders, or notify about
    schedule changes. The system will look up the customer's contact
    info automatically.

    Args:
        customer_id: The customer's unique ID.
        message: The notification text to send.
        channel: How to send it — 'sms' or 'email'. Defaults to 'sms'.

    Returns:
        A dict with delivery status and details.
    """
    valid_channels = {"sms", "email"}
    if channel not in valid_channels:
        return {"error": f"Invalid channel '{channel}'. Must be one of: {valid_channels}"}

    try:
        with get_connection() as conn:
            # Look up the customer's contact info
            cur = conn.execute(
                """
                SELECT id, name, phone, email
                FROM customers
                WHERE id = %(customer_id)s
                """,
                {"customer_id": customer_id},
            )
            row = cur.fetchone()

            if row is None:
                return {"error": f"Customer '{customer_id}' not found."}

            columns = [desc[0] for desc in cur.description]
            customer = dict(zip(columns, row))

        # Determine the delivery target
        if channel == "sms":
            target = customer.get("phone")
            if not target:
                return {"error": f"Customer '{customer['name']}' has no phone number on file."}
        else:
            target = customer.get("email")
            if not target:
                return {"error": f"Customer '{customer['name']}' has no email on file."}

        # Log the notification (actual SMS/email sending is handled by
        # the notification service — here we just record the intent)
        notification_id = str(uuid.uuid4())
        now = datetime.utcnow()

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO notifications (
                    id, customer_id, channel, target, message,
                    status, created_at
                ) VALUES (
                    %(id)s, %(customer_id)s, %(channel)s, %(target)s,
                    %(message)s, 'queued', %(now)s
                )
                """,
                {
                    "id": notification_id,
                    "customer_id": customer_id,
                    "channel": channel,
                    "target": target,
                    "message": message,
                    "now": now,
                },
            )
            conn.commit()

        logger.info(
            "Queued %s notification %s to customer %s (%s)",
            channel, notification_id, customer_id, target,
        )
        return {
            "notification_id": notification_id,
            "customer_id": customer_id,
            "customer_name": customer["name"],
            "channel": channel,
            "target": target,
            "message": message,
            "status": "queued",
        }

    except Exception as exc:
        logger.error("Failed to send notification: %s", exc)
        return {"error": f"Failed to send notification: {exc}"}
