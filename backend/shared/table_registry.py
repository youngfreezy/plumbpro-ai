"""Table registry -- ensures all database tables exist on startup.

Calls each store module's ``ensure_*_table()`` function in dependency order
(companies first, since other tables reference it via foreign keys).
"""

from __future__ import annotations

import logging

from backend.shared.stores.company_store import ensure_companies_table
from backend.shared.stores.customer_store import ensure_customers_table
from backend.shared.stores.user_store import ensure_users_table
from backend.shared.stores.job_store import ensure_jobs_table
from backend.shared.stores.session_store import ensure_agent_sessions_table

logger = logging.getLogger(__name__)


async def ensure_all_tables() -> None:
    """Create all tables in dependency order.

    Companies must be created first (parent table), then customers and
    users (which reference companies), then jobs (which references
    customers and users), then sessions (which references users and jobs).
    """
    await ensure_companies_table()
    await ensure_customers_table()
    await ensure_users_table()
    await ensure_jobs_table()
    await ensure_agent_sessions_table()
    logger.info("All PlumbPro tables ensured")
