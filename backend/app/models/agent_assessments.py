"""Structured, advisory outputs from the triage and evidence agents."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OrchestrationAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    normalized_title: str = Field(min_length=1, max_length=160)
    normalized_summary: str = Field(min_length=1, max_length=2000)
    normalized_location: str | None = Field(default=None, max_length=200)
    normalized_specific_location: str | None = Field(default=None, max_length=200)
    suggested_category_id: str | None = Field(default=None, max_length=100)
    suggested_department_id: str | None = Field(default=None, max_length=100)
    rationale: str = Field(min_length=1, max_length=2000)


class EvidenceAssessmentStatus(str, Enum):
    POTENTIALLY_RELEVANT = "potentially_relevant"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONTRADICTORY_EVIDENCE = "contradictory_evidence"


class EvidenceAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: EvidenceAssessmentStatus
    relevance_score: float = Field(ge=0, le=1)
    quality: Literal["good", "limited", "poor", "unassessed"]
    issues: list[str] = Field(default_factory=list, max_length=25)
    observations: list[str] = Field(default_factory=list, max_length=25)
    summary: str = Field(min_length=1, max_length=2000)
    requires_human_review: Literal[True] = True
