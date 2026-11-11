"""Authenticated endpoint for AI-assisted complaint routing advice."""

from fastapi import APIRouter, Depends, HTTPException

from app.agents.orchestrator_agent import OrchestratorAgent
from app.ai.multi_provider_client import AIProviderError
from app.auth.permissions import require_roles
from app.dependencies import get_department_repository
from app.models.conversation import ConfirmedComplaint
from app.models.user import AuthenticatedUser, UserRole
from app.repositories.department_repository import DepartmentRepository
from app.ai.hospital_context import build_hospital_context

router = APIRouter(prefix="/api/orchestrator", tags=["orchestration"])


@router.post("/assess")
async def assess_complaint(
    complaint: ConfirmedComplaint,
    current_user: AuthenticatedUser = Depends(require_roles([UserRole.HOSPITAL_ADMIN, UserRole.HIGHER_AUTHORITY])),
    department_repo: DepartmentRepository = Depends(get_department_repository),
):
    """Return a suggestion from the approved directory; this endpoint changes no records."""
    del current_user
    departments = department_repo.get_all_departments()
    categories = department_repo.get_all_categories()
    mappings = department_repo.get_all_mappings()
    context = build_hospital_context(categories, mappings, departments)
    try:
        result = await OrchestratorAgent().assess(
            complaint.model_dump(mode="json"),
            departments,
            hospital_context=context,
        )
    except AIProviderError:
        raise HTTPException(status_code=503, detail="Orchestration AI providers are unavailable.") from None
    selected_category_id = result.suggested_category_id
    if selected_category_id is None and complaint.category:
        selected_category_id = next((
            route["approved_category_id"]
            for route in context["service_routes"]
            if str(route["approved_category"]).casefold() == complaint.category.strip().casefold()
            and route.get("mapped_department_id")
        ), None)
    return {
        "assessment": result,
        "authoritative_route": next((
            {"department_id": route["mapped_department_id"], "department_name": route["mapped_department"]}
            for route in context["service_routes"]
            if str(route["approved_category_id"]) == str(selected_category_id)
            and route.get("mapped_department_id")
        ), None),
        "directory_source": "hospital_departments_and_category_mappings",
        "mutated_records": False,
    }
