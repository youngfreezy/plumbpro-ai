"""Domain configuration for customizing the platform to any service business.

The platform ships with a plumbing preset but can be reconfigured for HVAC,
electrical, landscaping, cleaning, or any field service business by changing
the domain config JSON file.
"""

import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class DomainConfig(BaseModel):
    """Configuration that customizes the platform for a specific business domain."""

    # Business identity
    business_type: str  # "plumbing", "hvac", "electrical", "landscaping", etc.
    app_name: str  # "PlumbPro AI", "HVAC Pro AI", etc.
    tagline: str  # "AI-powered plumbing business management"

    # Terminology (customizable labels)
    labels: dict  # Maps generic terms to domain-specific ones
    # e.g., {"technician": "Plumber", "job": "Service Call", "part": "Fitting", ...}

    # Service categories (replace hardcoded plumbing categories)
    job_categories: list[dict]  # [{"id": "drain", "label": "Drain Cleaning", "icon": "droplets"}, ...]

    # Priority levels (usually same across domains)
    priority_levels: list[dict]  # [{"id": "emergency", "label": "Emergency", "color": "red"}, ...]

    # Job statuses
    job_statuses: list[dict]  # [{"id": "pending", "label": "Pending", "color": "gray"}, ...]

    # Part categories (domain-specific)
    part_categories: list[str]  # ["pipes", "fittings", "valves", "fixtures", ...]

    # Agent system prompt context (injected into all agent prompts)
    domain_context: str  # Paragraph describing the business domain for LLM context

    # Diagnostic capabilities
    diagnostic_prompt_context: str  # Domain-specific diagnostic knowledge

    # Code/compliance context
    compliance_context: str  # Which codes/regulations apply

    # Default markup percentage
    default_markup_pct: float  # 50.0 for plumbing, etc.

    # Modules enabled (not all domains need all modules)
    enabled_modules: list[str]  # ["scheduling", "diagnostics", "estimates", ...]


# Load from JSON file
_config: Optional[DomainConfig] = None
_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "domain.json"


def get_domain_config() -> DomainConfig:
    global _config
    if _config is None:
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH) as f:
                _config = DomainConfig(**json.load(f))
        else:
            _config = _load_default_plumbing_config()
    return _config


def _load_default_plumbing_config() -> DomainConfig:
    """Default plumbing configuration."""
    return DomainConfig(
        business_type="plumbing",
        app_name="PlumbPro AI",
        tagline="AI-powered plumbing business management",
        labels={
            "technician": "Plumber",
            "technician_plural": "Plumbers",
            "job": "Service Call",
            "job_plural": "Service Calls",
            "part": "Part",
            "part_plural": "Parts",
            "customer": "Customer",
            "estimate": "Estimate",
            "invoice": "Invoice",
            "permit": "Permit",
            "certification": "License",
            "apprentice": "Apprentice",
            "owner": "Owner",
            "admin": "Office Manager",
        },
        job_categories=[
            {"id": "drain", "label": "Drain Cleaning", "icon": "droplets"},
            {"id": "water_heater", "label": "Water Heater", "icon": "flame"},
            {"id": "leak", "label": "Leak Repair", "icon": "droplet"},
            {"id": "sewer", "label": "Sewer Line", "icon": "waves"},
            {"id": "fixture", "label": "Fixture Install", "icon": "bath"},
            {"id": "gas", "label": "Gas Line", "icon": "zap"},
            {"id": "remodel", "label": "Remodel", "icon": "hammer"},
            {"id": "other", "label": "Other", "icon": "wrench"},
        ],
        priority_levels=[
            {"id": "emergency", "label": "Emergency", "color": "red"},
            {"id": "urgent", "label": "Urgent", "color": "orange"},
            {"id": "normal", "label": "Normal", "color": "blue"},
            {"id": "low", "label": "Low Priority", "color": "gray"},
        ],
        job_statuses=[
            {"id": "pending", "label": "Pending", "color": "gray"},
            {"id": "scheduled", "label": "Scheduled", "color": "blue"},
            {"id": "en_route", "label": "En Route", "color": "yellow"},
            {"id": "in_progress", "label": "In Progress", "color": "orange"},
            {"id": "completed", "label": "Completed", "color": "green"},
            {"id": "cancelled", "label": "Cancelled", "color": "red"},
        ],
        part_categories=[
            "pipes", "fittings", "valves", "fixtures",
            "water_heaters", "tools", "adhesives", "other",
        ],
        domain_context=(
            "You are an AI assistant for a plumbing business. You help manage scheduling, "
            "diagnostics, estimates, permits, inventory, customer communication, training, and documentation "
            "for residential and commercial plumbing services. You understand plumbing codes (IPC/UPC), "
            "common plumbing issues, parts and pricing, and industry best practices."
        ),
        diagnostic_prompt_context=(
            "When diagnosing plumbing issues, consider: pipe material and age, "
            "water pressure, drainage patterns, fixture types, code compliance, and common failure modes "
            "for the identified system. Reference IPC/UPC codes when applicable."
        ),
        compliance_context=(
            "Plumbing work is regulated by the International Plumbing Code (IPC) or "
            "Uniform Plumbing Code (UPC) depending on jurisdiction. Water heater installations, gas line work, "
            "and sewer connections typically require permits. Backflow prevention devices require annual testing."
        ),
        default_markup_pct=50.0,
        enabled_modules=[
            "scheduling", "diagnostics", "estimates", "permits",
            "inventory", "communication", "training", "documentation",
        ],
    )
