"""Central orchestrator: advisory classification only, never database authority."""

import json

from app.ai.multi_provider_client import MultiProviderClient
from app.models.agent_assessments import OrchestrationAssessment

_PROMPT = """You are the hospital's operational complaint triage assistant. The confirmed complaint may have been spoken in Kannada or another language. Always return normalized_title, normalized_summary, normalized_location, normalized_specific_location, and rationale in clear English. Translate the reported issue and location accurately; preserve facts and proper names, and never add unreported details. Use the live approved categories, category-to-department mappings, and operational handling guidance to return the ID of exactly one approved category that best matches the issue. Suggest the mapped department ID for that category only. Treat wards and rooms as locations, never as departments. If no category clearly fits, return a null category and department so the backend can request clarification; never invent a category or ID. Give practical non-clinical operational handling guidance in English. Never diagnose, prescribe, add unreported facts, promise an SLA, or claim an alert was sent. The backend mapping remains authoritative and controls the actual dashboard route."""


class OrchestratorAgent:
    def __init__(self, client: MultiProviderClient | None = None) -> None:
        self.client = client or MultiProviderClient("orchestrator")

    async def assess(
        self,
        complaint: dict,
        departments: list[dict],
        *,
        hospital_context: dict | None = None,
    ) -> OrchestrationAssessment:
        result = await self.client.complete(
            messages=[
                {"role": "system", "content": _PROMPT},
                {"role": "user", "content": json.dumps({
                    "complaint": complaint,
                    "approved_departments": departments,
                    "hospital_operational_context": hospital_context or {},
                }, ensure_ascii=False)},
            ],
            response_model=OrchestrationAssessment,
        )
        allowed = {str(item["id"]) for item in departments if item.get("id")}
        if result.suggested_department_id not in allowed:
            result.suggested_department_id = None
        category_id = result.suggested_category_id
        category_route = next((
            route
            for route in (hospital_context or {}).get("service_routes", [])
            if str(route.get("approved_category_id")) == str(category_id)
        ), None)
        if not category_route or not category_route.get("mapped_department_id"):
            result.suggested_category_id = None
            result.suggested_department_id = None
            return result
        mapped_owner = category_route.get("mapped_department_id")
        if str(mapped_owner) not in allowed:
            result.suggested_category_id = None
            result.suggested_department_id = None
        else:
            result.suggested_department_id = str(mapped_owner)
        return result
