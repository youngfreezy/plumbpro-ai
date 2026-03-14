"""Domain configuration API endpoint.

Serves the active domain configuration to the frontend so the UI can
adapt labels, categories, and branding to the configured business domain.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.shared.domain_config import get_domain_config

router = APIRouter(prefix="/api", tags=["domain"])


@router.get("/domain")
async def get_domain():
    """Return the active domain configuration.

    Public endpoint (no auth required) so the frontend can load branding
    and terminology on initial page load.
    """
    config = get_domain_config()
    return config.model_dump()
