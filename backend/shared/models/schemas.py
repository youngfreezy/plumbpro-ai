"""PlumbPro AI Pydantic models and enums for the plumbing business platform."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    EN_ROUTE = "en_route"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    NORMAL = "normal"
    LOW = "low"


class JobCategory(str, Enum):
    DRAIN = "drain"
    WATER_HEATER = "water_heater"
    LEAK = "leak"
    SEWER = "sewer"
    FIXTURE = "fixture"
    GAS = "gas"
    REMODEL = "remodel"
    OTHER = "other"


class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    TECHNICIAN = "technician"
    APPRENTICE = "apprentice"


class EstimateType(str, Enum):
    ESTIMATE = "estimate"
    INVOICE = "invoice"


class EstimateStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    DECLINED = "declined"
    PAID = "paid"
    OVERDUE = "overdue"


class PermitStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AgentModule(str, Enum):
    SCHEDULING = "scheduling"
    DIAGNOSTICS = "diagnostics"
    ESTIMATES = "estimates"
    PERMITS = "permits"
    INVENTORY = "inventory"
    COMMUNICATION = "communication"
    TRAINING = "training"
    DOCUMENTATION = "documentation"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------

class Company(BaseModel):
    id: Optional[str] = None
    name: str
    slug: str
    owner_email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    stripe_customer_id: Optional[str] = None
    subscription_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class User(BaseModel):
    id: Optional[str] = None
    company_id: str
    email: str
    name: str
    role: UserRole = UserRole.TECHNICIAN
    phone: Optional[str] = None
    password_hash: Optional[str] = None
    avatar_url: Optional[str] = None
    certifications: List[str] = Field(default_factory=list)
    is_active: bool = True
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Customer(BaseModel):
    id: Optional[str] = None
    company_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Job(BaseModel):
    id: Optional[str] = None
    company_id: str
    customer_id: Optional[str] = None
    assigned_technician_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: JobCategory = JobCategory.OTHER
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    estimate_id: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AgentSession(BaseModel):
    id: Optional[str] = None
    company_id: str
    user_id: str
    module: AgentModule
    job_id: Optional[str] = None
    status: str = "running"
    state_snapshot: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DiagnosticResult(BaseModel):
    id: Optional[str] = None
    job_id: str
    session_id: Optional[str] = None
    symptom_description: str
    probable_causes: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    parts_needed: List[str] = Field(default_factory=list)
    estimated_time_minutes: Optional[int] = None
    confidence_score: Optional[float] = None
    reference_codes: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class LineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float
    total: Optional[float] = None
    part_number: Optional[str] = None
    is_taxable: bool = True


class Estimate(BaseModel):
    id: Optional[str] = None
    company_id: str
    job_id: Optional[str] = None
    customer_id: Optional[str] = None
    estimate_type: EstimateType = EstimateType.ESTIMATE
    status: EstimateStatus = EstimateStatus.DRAFT
    line_items: List[LineItem] = Field(default_factory=list)
    subtotal: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    notes: Optional[str] = None
    valid_until: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PartsCatalogItem(BaseModel):
    id: Optional[str] = None
    company_id: str
    name: str
    part_number: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit_cost: float = 0.0
    markup_percent: float = 0.0
    retail_price: float = 0.0
    supplier_id: Optional[str] = None
    min_stock_level: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TruckInventoryItem(BaseModel):
    id: Optional[str] = None
    company_id: str
    technician_id: str
    part_id: str
    quantity: int = 0
    last_restocked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Supplier(BaseModel):
    id: Optional[str] = None
    company_id: str
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    account_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Permit(BaseModel):
    id: Optional[str] = None
    company_id: str
    job_id: Optional[str] = None
    permit_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    permit_number: Optional[str] = None
    status: PermitStatus = PermitStatus.PENDING
    application_date: Optional[datetime] = None
    approval_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    inspector_name: Optional[str] = None
    inspection_date: Optional[datetime] = None
    notes: Optional[str] = None
    documents: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class JobDocument(BaseModel):
    id: Optional[str] = None
    job_id: str
    company_id: str
    document_type: str  # "photo", "receipt", "permit", "report"
    file_url: str
    file_name: Optional[str] = None
    description: Optional[str] = None
    uploaded_by: Optional[str] = None
    created_at: Optional[datetime] = None


class Certification(BaseModel):
    id: Optional[str] = None
    user_id: str
    company_id: str
    name: str
    issuing_body: Optional[str] = None
    certificate_number: Optional[str] = None
    issued_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    document_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TrainingQuiz(BaseModel):
    id: Optional[str] = None
    company_id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    questions: List[Dict[str, Any]] = Field(default_factory=list)
    passing_score: float = 0.7
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CommunicationLog(BaseModel):
    id: Optional[str] = None
    company_id: str
    job_id: Optional[str] = None
    customer_id: Optional[str] = None
    user_id: Optional[str] = None
    channel: str  # "sms", "email", "phone", "in_app"
    direction: str  # "inbound", "outbound"
    subject: Optional[str] = None
    body: Optional[str] = None
    status: str = "sent"  # "sent", "delivered", "failed", "read"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class CustomerReview(BaseModel):
    id: Optional[str] = None
    company_id: str
    job_id: Optional[str] = None
    customer_id: Optional[str] = None
    technician_id: Optional[str] = None
    rating: int  # 1-5
    comment: Optional[str] = None
    is_public: bool = True
    response: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
