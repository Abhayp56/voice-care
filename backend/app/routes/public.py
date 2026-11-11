import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.services.publication_service import PublicationService
from app.dependencies import get_publication_service
from app.models.complaint import PublicComplaintResponse
from app.models.dashboard import PublicDepartmentStatsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/public", tags=["Public Transparency Portal"])


@router.get("/complaints", response_model=dict)
def get_public_complaints(
    department_name: Optional[str] = Query(None, description="Filter by department name (e.g. Sanitation)"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. resolved, in_progress)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: PublicationService = Depends(get_publication_service)
):
    """
    Public transparency complaints feed.
    Zero PII exposed: queries `public_complaints_view` (complaint_number, department_name, category_name, status, submission_date).
    Does NOT require authentication.
    """
    complaints, total = service.get_public_complaints(
        department_name=department_name,
        status=status,
        limit=limit,
        offset=offset
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "complaints": complaints
    }


@router.get("/complaints/{complaint_number}", response_model=PublicComplaintResponse)
def track_public_complaint(
    complaint_number: str,
    service: PublicationService = Depends(get_publication_service)
):
    """
    Public grievance status tracking.
    Enables patients to verify complaint progress via their tracking ID (e.g. VC-2026-0001).
    Exposes no patient names, phone numbers, or private audio recordings.
    """
    result = service.get_public_tracking_status(complaint_number)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Public tracking record for '{complaint_number}' not found."
        )
    return result


@router.get("/department-statistics", response_model=List[PublicDepartmentStatsResponse])
def get_public_department_statistics(
    service: PublicationService = Depends(get_publication_service)
):
    """
    Public department accountability statistics from `public_department_statistics`.
    Returns aggregate counts per department (total, resolved, open) for civic monitoring.
    """
    return service.get_public_department_statistics()
