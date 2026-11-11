"""Multimodal evidence analysis; it cannot approve or resolve a complaint."""

import json

from app.ai.multi_provider_client import MultiProviderClient
from app.models.agent_assessments import EvidenceAssessment, EvidenceAssessmentStatus

_PROMPT = """Assess whether the supplied resolution photograph appears relevant to the complaint and resolution note. Photos can be staged, old, or misleading; do not claim authenticity, capture time, location, or completed work. State uncertainty and observable limitations. Always return requires_human_review=true. AI output must never approve or resolve the complaint."""


class VerificationAgent:
    def __init__(self, client: MultiProviderClient | None = None) -> None:
        self.client = client or MultiProviderClient("verification")

    async def analyze(self, *, complaint: dict, evidence_note: str | None, image: bytes, media_type: str) -> EvidenceAssessment:
        return await self.client.complete(
            messages=[
                {"role": "system", "content": _PROMPT},
                {"role": "user", "content": json.dumps({"complaint": complaint, "resolution_note": evidence_note or ""}, ensure_ascii=False)},
            ],
            response_model=EvidenceAssessment,
            images=[(image, media_type)],
        )


def unavailable_assessment(reason: str) -> EvidenceAssessment:
    return EvidenceAssessment(
        status=EvidenceAssessmentStatus.INSUFFICIENT_EVIDENCE,
        relevance_score=0,
        quality="unassessed",
        issues=[reason],
        summary="Automated analysis was unavailable. A human must review the evidence.",
        requires_human_review=True,
    )
