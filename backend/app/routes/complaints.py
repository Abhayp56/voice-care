import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.status_history_repository import StatusHistoryRepository
from app.dependencies import (
    get_complaint_repository,
    get_department_repository,
    get_status_history_repository
)
from app.auth.authentication import get_current_user
from app.auth.permissions import check_complaint_access, check_department_access, check_status_update_permission
from app.models.complaint import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintStatusUpdate,
    ComplaintStatus,
)
from app.models.status_history import StatusHistoryResponse
from app.models.user import AuthenticatedUser, UserRole
from app.services.complaint_intake import create_complaint_record
from app.database.supabase_client import get_supabase_client
from app.auth.permissions import require_roles
from app.services.complaint_deadlines import escalation_metadata, is_higher_authority_case
from app.repositories.evidence_repository import EvidenceRepository
from app.dependencies import get_evidence_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def create_complaint(
    payload: ComplaintCreate,
    complaint_repo: ComplaintRepository = Depends(get_complaint_repository),
    dept_repo: DepartmentRepository = Depends(get_department_repository),
    history_repo: StatusHistoryRepository = Depends(get_status_history_repository)
):
    """
    Create a new complaint record.
    Primary ingestion endpoint for AI Patient Conversation Agent & Central Orchestrator.
    
    Features:
    - Validates category existence.
    - Auto-routes to correct department via department_mapping if department_id is omitted.
    - Uses category default_priority if priority is omitted.
    - Generates atomic complaint number (e.g. VC-2026-0006) using existing counter.
    - Automatically records initial status_history entry.
    """
    return create_complaint_record(
        payload,
        complaint_repo=complaint_repo,
        dept_repo=dept_repo,
        history_repo=history_repo,
    )


@router.get("", response_model=dict)
def list_complaints(
    department_id: Optional[str] = Query(None, description="Filter by department UUID"),
    status: Optional[str] = Query(None, description="Filter by status (received, in_progress, resolved, etc.)"),
    priority: Optional[str] = Query(None, description="Filter by priority (low, medium, high, critical)"),
    category_id: Optional[str] = Query(None, description="Filter by category UUID"),
    search: Optional[str] = Query(None, description="Search keyword in description"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    complaint_repo: ComplaintRepository = Depends(get_complaint_repository),
    evidence_repo: EvidenceRepository = Depends(get_evidence_repository),
):
    """
    Search and list complaints with pagination and filtering.
    Enforces role-based isolation:
    - Department staff/heads are locked to their assigned department.
    - Hospital admins and higher authorities can view across all departments.
    """
    # Department staff isolation
    effective_dept_id = department_id
    if current_user.role == UserRole.DEPARTMENT_HEAD:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User profile has no assigned department."
            )
        if department_id and department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot view complaints from other departments."
            )
        effective_dept_id = current_user.department_id

    is_higher = current_user.role == UserRole.HIGHER_AUTHORITY
    complaints, total = complaint_repo.get_complaints(
        department_id=None if is_higher else effective_dept_id,
        status=status,
        priority=priority,
        category_id=category_id,
        assigned_to=None,
        search_query=search,
        older_than_days=11 if is_higher else None,
        open_only=is_higher,
        limit=limit,
        offset=offset
    )

    for item in complaints:
        item.update(escalation_metadata(item))
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "complaints": complaints
    }


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(
    complaint_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    complaint_repo: ComplaintRepository = Depends(get_complaint_repository),
):
    """
    Retrieve single complaint by internal UUID or complaint_number (e.g. VC-2026-0001).
    Enforces department isolation.
    """
    complaint = complaint_repo.get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found."
        )

    # Enforce department access
    check_complaint_access(current_user, complaint)
    return complaint


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def update_complaint_status(
    complaint_id: str,
    payload: ComplaintStatusUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    complaint_repo: ComplaintRepository = Depends(get_complaint_repository),
    evidence_repo: EvidenceRepository = Depends(get_evidence_repository),
):
    """
    Update complaint status, save resolution notes, and maintain history trail.
    Enforces role & department permissions.
    """
    complaint = complaint_repo.get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found."
        )

    # Enforce department access
    check_complaint_access(current_user, complaint)

    check_status_update_permission(current_user, payload.status.value)

    age = escalation_metadata(complaint)["days_open"]
    if payload.status in {ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED}:
        if current_user.role == UserRole.HIGHER_AUTHORITY and age < 11:
            raise HTTPException(status_code=403, detail="Higher Authority can submit only complaints open for at least 11 days.")
        if current_user.role in {UserRole.DEPARTMENT_HEAD, UserRole.HOSPITAL_ADMIN} and age >= 11:
            raise HTTPException(status_code=403, detail="Complaints open for 11 days must be submitted by Higher Authority.")
        evidences = evidence_repo.get_evidence_by_complaint(complaint["id"])
        if not evidences or not evidences[0].get("verified_at") or not evidence_repo.has_ai_analysis(evidences[0]["id"]):
            raise HTTPException(status_code=409, detail="Resolution requires a GPS-tagged photo, AI advisory, and human verification.")

    updated = complaint_repo.update_complaint_status(
        complaint_id=complaint["id"],
        new_status=payload.status.value,
        note=payload.note,
        changed_by=current_user.id
    )

    # Return refreshed joined record
    refreshed = complaint_repo.get_complaint_by_id(complaint["id"])
    return refreshed or updated


@router.get("/{complaint_id}/history", response_model=List[StatusHistoryResponse])
def get_complaint_history(
    complaint_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    complaint_repo: ComplaintRepository = Depends(get_complaint_repository),
    history_repo: StatusHistoryRepository = Depends(get_status_history_repository)
):
    """Retrieve the full status transition and note history for a complaint."""
    complaint = complaint_repo.get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found."
        )

    check_complaint_access(current_user, complaint)
    return history_repo.get_history_by_complaint(complaint["id"])


@router.get("/{complaint_id}/lifecycle")
def get_complaint_lifecycle(
    complaint_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    complaint_repo: ComplaintRepository = Depends(get_complaint_repository),
):
    """Read persisted lifecycle timestamps and the configured resolution deadline."""
    complaint = complaint_repo.get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    check_complaint_access(current_user, complaint)
    client = get_supabase_client()
    lifecycle = client.table("complaint_lifecycle_records").select("*").eq("complaint_id", complaint["id"]).maybe_single().execute()
    events = client.table("complaint_lifecycle_events").select("old_status,new_status,actor_id,note,occurred_at").eq("complaint_id", complaint["id"]).order("occurred_at").execute()
    return {"lifecycle": lifecycle.data, "events": events.data or [], "sla_configured": bool(lifecycle.data and lifecycle.data.get("resolution_due_at"))}
