"""Centralised configuration loaded from environment / .env file."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

# Resolve project root (.env lives at the repo root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings.

    Values are read from environment variables first, then from a ``.env``
    file in the project root.  Every field that has a default can be omitted
    from the environment; required fields (no default) must be present at
    startup.
    """

    # --- LLM ---
    LLM_PROVIDER: str = "openai"  # "openai" or "anthropic"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_DEFAULT_MODEL: str = "gpt-5-mini"
    OPENAI_PREMIUM_MODEL: str = "gpt-5"
    OPENAI_BROWSER_MODEL: str = "gpt-5-mini"
    ANTHROPIC_DEFAULT_MODEL: str = "claude-sonnet-4-6"
    ANTHROPIC_PREMIUM_MODEL: str = "claude-opus-4-6"
    ANTHROPIC_LIGHT_MODEL: str = "claude-haiku-4-5-20251001"
    ANTHROPIC_BROWSER_MODEL: str = "claude-sonnet-4-5"

    # --- Postgres ---
    DATABASE_URL: str = "postgresql://plumbpro:change_me@localhost:5435/plumbpro"

    # --- Redis ---
    REDIS_URL: str = "redis://:change_me@localhost:6381"

    # --- Auth ---
    NEXTAUTH_SECRET: Optional[str] = None

    # --- Stripe ---
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # --- Email ---
    RESEND_API_KEY: Optional[str] = None

    # --- Twilio SMS ---
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # --- Google Maps (routing / address lookup) ---
    GOOGLE_MAPS_API_KEY: Optional[str] = None

    # --- S3 (photo storage) ---
    S3_BUCKET: Optional[str] = None
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # --- LangSmith ---
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "plumbpro-ai"

    # --- Observability ---
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": (
            str(_PROJECT_ROOT / ".env"),
            str(_PROJECT_ROOT / ".env.local"),
        ),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton – import this everywhere instead of re-instantiating.
settings = Settings()  # type: ignore[call-arg]


def get_settings() -> Settings:
    """Return the module-level Settings singleton.

    Provided as a convenience so agents can call ``get_settings()`` without
    importing the bare ``settings`` object directly.
    """
    return settings
