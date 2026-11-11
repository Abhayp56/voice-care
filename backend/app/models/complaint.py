from datetime import datetime, date
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field


class ComplaintStatus(str, Enum):
    RECEIVED = "received"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    NEEDS_REVIEW = "needs_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class ComplaintPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplaintBase(BaseModel):
    description: str = Field(..., min_length=5, description="Full grievance description transcribed from voice conversation")
    language: str = Field(default="en", description="ISO language code of voice interaction (e.g. en, kn, hi)")
    category_id: str = Field(..., description="UUID of complaint category")
    department_id: Optional[str] = Field(None, description="Ignored on intake; backend routes from the trusted category mapping.")
    priority: Optional[ComplaintPriority] = Field(None, description="Ignored on intake; priority comes from the trusted category default.")
    patient_name: Optional[str] = Field(None, max_length=255, description="Patient full name (Private PII)")
    patient_phone: Optional[str] = Field(None, max_length=50, description="Patient contact number (Private PII)")


class ComplaintCreate(ComplaintBase):
    """Payload provided by AI Central Orchestrator / Patient Conversation Agent"""
    pass


class ComplaintUpdate(BaseModel):
    priority: Optional[ComplaintPriority] = None
    department_id: Optional[str] = None
    assigned_to: Optional[str] = None
    status: Optional[ComplaintStatus] = None


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatus = Field(..., description="New complaint status")
    note: Optional[str] = Field(None, description="Resolution or transition notes explaining the change")


class ComplaintResponse(BaseModel):
    id: str
    complaint_number: str
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    description: str
    language: str
    category_id: str
    department_id: str
    priority: str
    status: str
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # Expanded join fields
    department_name: Optional[str] = None
    category_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    days_open: int = 0
    warning_level: int = 0
    escalation_stage: str = "none"
    higher_authority_review: bool = False
    latest_authority_note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PublicComplaintResponse(BaseModel):
    """
    Public transparency representation.
    NEVER exposes patient_name, patient_phone, internal notes, or raw IDs.
    """
    complaint_number: str
    department_name: Optional[str] = None
    category_name: Optional[str] = None
    status: str
    submission_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

