"""Validated patient conversation request and response contracts."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.agent_assessments import OrchestrationAssessment


class ConversationState(str, Enum):
    STARTED = "STARTED"
    COLLECTING_INFORMATION = "COLLECTING_INFORMATION"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    SUBMITTED = "SUBMITTED"
    EMERGENCY_REDIRECTED = "EMERGENCY_REDIRECTED"
    CANCELLED = "CANCELLED"


class ConversationLanguage(str, Enum):
    KANNADA = "kn-IN"
    ENGLISH = "en-IN"


class ComplaintCategory(str, Enum):
    SANITATION = "Sanitation"
    CLEANLINESS = "Cleanliness"
    WAITING_TIME = "Waiting time"
    STAFF_CONDUCT = "Staff conduct"
    FACILITIES = "Facilities"
    ACCESSIBILITY = "Accessibility"
    BILLING = "Billing"
    OTHER = "Other"


class ComplaintField(str, Enum):
    TITLE = "title"
    DESCRIPTION = "description"
    CATEGORY = "category"
    LOCATION = "location"
    SPECIFIC_LOCATION = "specific_location"


class PrioritySuggestion(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ComplaintFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=200)
    specific_location: str | None = Field(default=None, max_length=200)
    priority_suggestion: PrioritySuggestion | None = None


class ConversationAgentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: ConversationLanguage
    reply: str = Field(min_length=1, max_length=2500)
    facts: ComplaintFacts = Field(default_factory=ComplaintFacts)
    missing_information: list[ComplaintField] = Field(default_factory=list, max_length=5)
    summary: str | None = Field(default=None, max_length=1000)
    ready_for_confirmation: bool = False
    emergency_redirect: bool = False
    cancelled: bool = False

    @model_validator(mode="after")
    def validate_confirmation_summary(self) -> "ConversationAgentResponse":
        if self.ready_for_confirmation and not self.summary:
            raise ValueError("A summary is required before asking for confirmation")
        if self.emergency_redirect and self.ready_for_confirmation:
            raise ValueError("Emergency redirection cannot request complaint confirmation")
        return self


class StartConversationRequest(BaseModel):
    language: ConversationLanguage = ConversationLanguage.ENGLISH


class StartConversationResponse(BaseModel):
    session_id: str
    state: ConversationState
    language: ConversationLanguage
    reply: str
    expires_in_seconds: int


class ConversationMessageRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=4000)


class ConfirmConversationRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    confirmed: bool
    correction: str | None = Field(default=None, max_length=2000)


class ConfirmedComplaint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = ""
    description: str
    category: str | None = Field(default=None, min_length=1, max_length=120)
    location: str = ""
    specific_location: str | None = None
    language: ConversationLanguage
    priority_suggestion: PrioritySuggestion | None = None
    missing_information: list[ComplaintField] = Field(default_factory=list)
    patient_confirmed: Literal[True] = True


class ConversationResponse(BaseModel):
    session_id: str
    state: ConversationState
    language: ConversationLanguage
    reply: str
    summary: str | None = None
    draft: ComplaintFacts | None = None
    missing_information: list[ComplaintField] = Field(default_factory=list)
    complaint: ConfirmedComplaint | None = None


class ConversationSubmissionResponse(BaseModel):
    session_id: str
    state: Literal[ConversationState.SUBMITTED]
    complaint_id: str
    complaint_number: str
    routed_category: str
    routed_department: str
    routing_assessment: OrchestrationAssessment | None = None
