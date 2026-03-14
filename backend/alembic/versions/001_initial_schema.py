"""Initial schema — all core PlumbPro AI tables.

Revision ID: 001
Revises:
Create Date: 2026-03-14
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # pgcrypto for gen_random_uuid()
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ------------------------------------------------------------------
    # companies
    # ------------------------------------------------------------------
    op.create_table(
        "companies",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(50), nullable=True),
        sa.Column("zip_code", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("license_number", sa.String(100), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("settings", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("subscription_tier", sa.String(50), server_default="free", nullable=False),
        sa.Column("subscription_status", sa.String(50), server_default="active", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="technician"),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("preferences", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_company_id", "users", ["company_id"])

    # ------------------------------------------------------------------
    # customers
    # ------------------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(50), nullable=True),
        sa.Column("zip_code", sa.String(20), nullable=True),
        sa.Column("lat", sa.Float, nullable=True),
        sa.Column("lng", sa.Float, nullable=True),
        sa.Column("property_type", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("tags", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_customers_company_id", "customers", ["company_id"])
    op.create_index("ix_customers_email", "customers", ["company_id", "email"])
    op.create_index("ix_customers_phone", "customers", ["company_id", "phone"])

    # ------------------------------------------------------------------
    # jobs
    # ------------------------------------------------------------------
    op.create_table(
        "jobs",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", UUID, sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_to", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("job_type", sa.String(100), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(50), nullable=True),
        sa.Column("zip_code", sa.String(20), nullable=True),
        sa.Column("lat", sa.Float, nullable=True),
        sa.Column("lng", sa.Float, nullable=True),
        sa.Column("scheduled_start", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("scheduled_end", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("actual_start", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("actual_end", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("estimated_duration_min", sa.Integer, nullable=True),
        sa.Column("tags", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"])
    op.create_index("ix_jobs_status", "jobs", ["company_id", "status"])
    op.create_index("ix_jobs_assigned_to", "jobs", ["assigned_to"])
    op.create_index("ix_jobs_customer_id", "jobs", ["customer_id"])
    op.create_index("ix_jobs_scheduled_start", "jobs", ["company_id", "scheduled_start"])

    # ------------------------------------------------------------------
    # agent_sessions
    # ------------------------------------------------------------------
    op.create_table(
        "agent_sessions",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("job_id", UUID, sa.ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agent_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="running"),
        sa.Column("input_data", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("output_data", JSONB, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("tokens_used", sa.Integer, server_default=sa.text("0"), nullable=False),
        sa.Column("cost_cents", sa.Integer, server_default=sa.text("0"), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_agent_sessions_company_id", "agent_sessions", ["company_id"])
    op.create_index("ix_agent_sessions_job_id", "agent_sessions", ["job_id"])
    op.create_index("ix_agent_sessions_status", "agent_sessions", ["status"])

    # ------------------------------------------------------------------
    # diagnostics
    # ------------------------------------------------------------------
    op.create_table(
        "diagnostics",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", UUID, sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_session_id", UUID, sa.ForeignKey("agent_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("symptom_description", sa.Text, nullable=False),
        sa.Column("photo_urls", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("ai_diagnosis", JSONB, nullable=True),
        sa.Column("confirmed_diagnosis", sa.Text, nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("parts_recommended", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_diagnostics_job_id", "diagnostics", ["job_id"])
    op.create_index("ix_diagnostics_company_id", "diagnostics", ["company_id"])

    # ------------------------------------------------------------------
    # estimates
    # ------------------------------------------------------------------
    op.create_table(
        "estimates",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", UUID, sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", UUID, sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("diagnostic_id", UUID, sa.ForeignKey("diagnostics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("estimate_number", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("line_items", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("labor_hours", sa.Float, nullable=True),
        sa.Column("labor_rate", sa.Float, nullable=True),
        sa.Column("parts_total", sa.Float, nullable=True),
        sa.Column("labor_total", sa.Float, nullable=True),
        sa.Column("tax_rate", sa.Float, nullable=True),
        sa.Column("tax_amount", sa.Float, nullable=True),
        sa.Column("total", sa.Float, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("customer_approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("valid_until", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_estimates_company_id", "estimates", ["company_id"])
    op.create_index("ix_estimates_job_id", "estimates", ["job_id"])
    op.create_index("ix_estimates_customer_id", "estimates", ["customer_id"])
    op.create_index("ix_estimates_status", "estimates", ["company_id", "status"])

    # ------------------------------------------------------------------
    # parts_catalog
    # ------------------------------------------------------------------
    op.create_table(
        "parts_catalog",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sku", sa.String(100), nullable=True),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("unit_cost", sa.Float, nullable=True),
        sa.Column("retail_price", sa.Float, nullable=True),
        sa.Column("supplier_id", UUID, nullable=True),
        sa.Column("supplier_part_number", sa.String(100), nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column("specifications", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_parts_catalog_company_id", "parts_catalog", ["company_id"])
    op.create_index("ix_parts_catalog_sku", "parts_catalog", ["company_id", "sku"])
    op.create_index("ix_parts_catalog_category", "parts_catalog", ["company_id", "category"])

    # ------------------------------------------------------------------
    # truck_inventory
    # ------------------------------------------------------------------
    op.create_table(
        "truck_inventory",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("part_id", UUID, sa.ForeignKey("parts_catalog.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("min_quantity", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("truck_identifier", sa.String(100), nullable=True),
        sa.Column("last_restocked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_truck_inventory_company_user", "truck_inventory", ["company_id", "user_id"])
    op.create_index("ix_truck_inventory_part_id", "truck_inventory", ["part_id"])

    # ------------------------------------------------------------------
    # suppliers
    # ------------------------------------------------------------------
    op.create_table(
        "suppliers",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("account_number", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_suppliers_company_id", "suppliers", ["company_id"])

    # Add FK from parts_catalog to suppliers now that suppliers table exists
    op.create_foreign_key(
        "fk_parts_catalog_supplier_id",
        "parts_catalog",
        "suppliers",
        ["supplier_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ------------------------------------------------------------------
    # permits
    # ------------------------------------------------------------------
    op.create_table(
        "permits",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", UUID, sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permit_type", sa.String(100), nullable=False),
        sa.Column("permit_number", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("issuing_authority", sa.String(255), nullable=True),
        sa.Column("filed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("cost", sa.Float, nullable=True),
        sa.Column("document_url", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_permits_company_id", "permits", ["company_id"])
    op.create_index("ix_permits_job_id", "permits", ["job_id"])
    op.create_index("ix_permits_status", "permits", ["company_id", "status"])

    # ------------------------------------------------------------------
    # job_documents
    # ------------------------------------------------------------------
    op.create_table(
        "job_documents",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", UUID, sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=True),
        sa.Column("s3_key", sa.String(500), nullable=False),
        sa.Column("document_type", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_job_documents_job_id", "job_documents", ["job_id"])
    op.create_index("ix_job_documents_company_id", "job_documents", ["company_id"])

    # ------------------------------------------------------------------
    # certifications
    # ------------------------------------------------------------------
    op.create_table(
        "certifications",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("issuing_body", sa.String(255), nullable=True),
        sa.Column("cert_number", sa.String(100), nullable=True),
        sa.Column("issued_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("document_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_certifications_company_user", "certifications", ["company_id", "user_id"])
    op.create_index("ix_certifications_expires_at", "certifications", ["expires_at"])

    # ------------------------------------------------------------------
    # training_quizzes
    # ------------------------------------------------------------------
    op.create_table(
        "training_quizzes",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_session_id", UUID, sa.ForeignKey("agent_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("questions", JSONB, nullable=False),
        sa.Column("answers", JSONB, nullable=True),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("max_score", sa.Float, nullable=True),
        sa.Column("passed", sa.Boolean, nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_training_quizzes_company_user", "training_quizzes", ["company_id", "user_id"])
    op.create_index("ix_training_quizzes_topic", "training_quizzes", ["company_id", "topic"])

    # ------------------------------------------------------------------
    # customer_reviews
    # ------------------------------------------------------------------
    op.create_table(
        "customer_reviews",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", UUID, sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", UUID, sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rating", sa.SmallInteger, nullable=False),
        sa.Column("review_text", sa.Text, nullable=True),
        sa.Column("sentiment_score", sa.Float, nullable=True),
        sa.Column("ai_summary", sa.Text, nullable=True),
        sa.Column("is_public", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("response_text", sa.Text, nullable=True),
        sa.Column("responded_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_customer_reviews_company_id", "customer_reviews", ["company_id"])
    op.create_index("ix_customer_reviews_job_id", "customer_reviews", ["job_id"])
    op.create_index("ix_customer_reviews_rating", "customer_reviews", ["company_id", "rating"])

    # ------------------------------------------------------------------
    # communication_log
    # ------------------------------------------------------------------
    op.create_table(
        "communication_log",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", UUID, sa.ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("customer_id", UUID, sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("from_address", sa.String(255), nullable=True),
        sa.Column("to_address", sa.String(255), nullable=True),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("ai_generated", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("ai_draft", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="sent"),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_communication_log_company_id", "communication_log", ["company_id"])
    op.create_index("ix_communication_log_job_id", "communication_log", ["job_id"])
    op.create_index("ix_communication_log_customer_id", "communication_log", ["customer_id"])
    op.create_index("ix_communication_log_channel", "communication_log", ["company_id", "channel"])


def downgrade() -> None:
    op.drop_table("communication_log")
    op.drop_table("customer_reviews")
    op.drop_table("training_quizzes")
    op.drop_table("certifications")
    op.drop_table("job_documents")
    op.drop_table("permits")
    op.drop_constraint("fk_parts_catalog_supplier_id", "parts_catalog", type_="foreignkey")
    op.drop_table("suppliers")
    op.drop_table("truck_inventory")
    op.drop_table("parts_catalog")
    op.drop_table("estimates")
    op.drop_table("diagnostics")
    op.drop_table("agent_sessions")
    op.drop_table("jobs")
    op.drop_table("customers")
    op.drop_table("users")
    op.drop_table("companies")
