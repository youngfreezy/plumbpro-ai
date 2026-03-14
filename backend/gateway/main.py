"""FastAPI gateway for the PlumbPro AI platform.

Provides the REST + SSE API that the Next.js frontend consumes.
Manages the LangGraph pipeline lifecycle, SSE streaming, and HITL flow.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging for all backend modules
_log_fmt = logging.Formatter("%(levelname)s %(name)s: %(message)s")
_console = logging.StreamHandler()
_console.setFormatter(_log_fmt)
_handlers: list[logging.Handler] = [_console]
if os.environ.get("LOG_TO_FILE", "true").lower() == "true":
    _file = logging.FileHandler("backend.log", mode="a")
    _file.setFormatter(_log_fmt)
    _handlers.append(_file)
logging.basicConfig(level=logging.INFO, handlers=_handlers)
for _noisy in (
    "httpcore", "httpx", "urllib3", "watchfiles", "asyncio",
    "langgraph.checkpoint.serde.jsonplus",
):
    logging.getLogger(_noisy).setLevel(logging.ERROR)

from backend.shared.config import get_settings

logger = logging.getLogger(__name__)

# --- Sentry error tracking ---
_settings = get_settings()
if _settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=_settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                LoggingIntegration(level=logging.WARNING, event_level=logging.ERROR),
            ],
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
        logger.info("Sentry initialized")
    except ImportError:
        logger.warning("sentry-sdk not installed -- error tracking disabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle.

    1. Connect Redis
    2. Init DB pool / ensure tables
    3. Build LangGraph router
    4. Attach to app.state
    """
    settings = get_settings()
    logger.info("Starting PlumbPro AI gateway (log_level=%s)", settings.LOG_LEVEL)

    # --- Build the LangGraph router pipeline ---
    from backend.orchestrator.router.graph import build_router

    # --- Checkpointer: prefer Postgres, fall back to in-memory ---
    checkpointer = None
    pool = None
    try:
        from psycopg import AsyncConnection
        from psycopg_pool import AsyncConnectionPool
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        # Setup with autocommit connection (CREATE INDEX CONCURRENTLY
        # cannot run inside a transaction block)
        try:
            async with await AsyncConnection.connect(
                settings.DATABASE_URL, autocommit=True
            ) as setup_conn:
                setup_saver = AsyncPostgresSaver(setup_conn)
                await setup_saver.setup()
        except Exception as setup_exc:
            logger.warning("Checkpointer setup() failed (%s); tables may already exist", setup_exc)

        pool = AsyncConnectionPool(
            conninfo=settings.DATABASE_URL,
            min_size=2,
            max_size=20,
            open=False,
        )
        await pool.open()
        checkpointer = AsyncPostgresSaver(pool)
        logger.info("Using AsyncPostgresSaver with connection pool")

        # Ensure all store tables exist
        from backend.shared.table_registry import ensure_all_tables
        await ensure_all_tables()

    except Exception as exc:
        logger.warning(
            "Postgres checkpointer unavailable (%s); falling back to MemorySaver",
            exc,
        )
        pool = None
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()

    graph = build_router(checkpointer=checkpointer)

    # --- Redis ---
    from backend.shared.redis_client import redis_client
    try:
        await redis_client.connect()
    except Exception as exc:
        logger.warning("Redis connection failed (%s) -- rate limiting disabled", exc)

    # Attach to app.state so route handlers can access them
    app.state.graph = graph
    app.state.checkpointer = checkpointer
    app.state.settings = settings

    yield

    # --- Shutdown ---
    logger.info("Shutting down PlumbPro AI gateway")

    try:
        await redis_client.close()
    except Exception:
        pass

    from backend.shared.db import close_pool
    close_pool()

    if pool is not None:
        await pool.close()
    elif hasattr(checkpointer, "close"):
        await checkpointer.close()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="PlumbPro AI API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # --- CORS ---
    _origins = [
        "http://localhost:5100",
        "https://localhost:5100",
    ]
    _extra_origins = os.environ.get("CORS_ORIGINS", "")
    if _extra_origins:
        _origins.extend(o.strip() for o in _extra_origins.split(",") if o.strip())

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_origin_regex=r"https://(plumbpro(-[a-z0-9]+)?\.vercel\.app|([a-z]+-)+[a-z0-9]+\.up\.railway\.app|([a-z]+\.)?plumbpro\.ai)",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Starlette middleware execution order is REVERSED from registration.
    # Last registered = first to run on incoming request.
    # Desired request flow: JWT Auth -> CSRF -> Rate Limiter -> Route
    # So register in reverse:

    from backend.gateway.middleware.rate_limit import attach_rate_limiter
    attach_rate_limiter(app)

    from backend.gateway.middleware.csrf import attach_csrf_protection
    attach_csrf_protection(app)

    from backend.gateway.middleware.jwt_auth import attach_jwt_auth
    attach_jwt_auth(app)

    # --- Routes ---
    from backend.gateway.routes.health import router as health_router
    from backend.gateway.routes.auth import router as auth_router
    from backend.gateway.routes.jobs import router as jobs_router
    from backend.gateway.routes.customers import router as customers_router
    from backend.gateway.routes.scheduling import router as scheduling_router
    from backend.gateway.routes.agent_sessions import router as agent_router
    from backend.gateway.routes.domain import router as domain_router

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(jobs_router)
    app.include_router(customers_router)
    app.include_router(scheduling_router)
    app.include_router(agent_router)
    app.include_router(domain_router)

    return app


app = create_app()
