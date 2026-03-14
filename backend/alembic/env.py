"""Alembic environment configuration.

Reads DATABASE_URL from the application Settings singleton and runs
migrations using the psycopg (async-capable) dialect.
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool

# Ensure the project root is on sys.path so that `backend.*` imports work
# when running `alembic` from the repo root.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend.shared.config import get_settings  # noqa: E402

# Alembic Config object — gives access to alembic.ini values.
config = context.config

# Set up Python logging from the ini file.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No declarative Base / MetaData target — we use raw SQL migrations.
target_metadata = None


def get_url() -> str:
    """Return the database URL, converting asyncpg:// to psycopg:// if needed."""
    url = get_settings().DATABASE_URL
    # Alembic needs a synchronous driver.  Swap async prefixes.
    if url.startswith("postgresql+asyncpg"):
        url = url.replace("postgresql+asyncpg", "postgresql+psycopg", 1)
    elif url.startswith("postgresql://"):
        # Default psycopg driver works fine.
        pass
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emit SQL to stdout."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = create_engine(
        get_url(),
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
