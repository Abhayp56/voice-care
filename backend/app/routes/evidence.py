import logging
import mimetypes
from pathlib import PurePath
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.services.storage_service import StorageService
from app.dependencies import (
    get_complaint_repository,
    get_evidence_repository,
    get_storage_service
)
from app.auth.authentication import get_current_user
from app.auth.permissions import check_complaint_access, require_roles
from app.models.evidence import EvidenceResponse, EvidenceVerificationRequest
from app.models.user import AuthenticatedUser, UserRole
from app.agents.verification_agent import VerificationAgent
from app.ai.multi_provider_client import AIProviderError
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Evidence & Photographs"])


@router.post("/evidence/{evidence_id}/analyze")
async def analyze_evidence(
    evidence_id: str,
    current_user: AuthenticatedUser = Depends(require_roles([UserRole.DEPARTMENT_HEAD, UserRole.HOSPITAL_ADMIN, UserRole.HIGHER_AUTHORITY])),
    evidence_repo: EvidenceRepository = Depends(get_evidence_repository),
    complaint_repo: ComplaintRepository = Depends(get_complaint_repository),
    storage_service: StorageService = Depends(get_storage_service),
):
    """Return and persist an AI advisory; human verification remains separate."""
    evidence = evidence_repo.get_evidence_by_id(evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    complaint = complaint_repo.get_complaint_by_id(evidence["complaint_id"])
    if not complaint:
        raise HTTPException(status_code=404, detail="Associated complaint not found")
    check_complaint_access(current_user, complaint)
    image = await run_in_threadpool(storage_service.download_evidence, evidence["file_path"])
    media_type = mimetypes.guess_type(PurePath(evidence["file_path"]).name)[0] or "image/jpeg"
    try:
        result = await VerificationAgent().analyze(
            complaint={
                "description": complaint.get("description", ""),
                "category": complaint.get("category_name", ""),
                "department": complaint.get("department_name", ""),
            },
            evidence_note=evidence.get("notes"),
            image=image,
            media_type=media_type,
        )
    except AIProviderError:
        raise HTTPException(status_code=503, detail="Evidence analysis providers are unavailable.") from None
    try:
        saved = await run_in_threadpool(
            evidence_repo.record_ai_analysis,
            evidence_id,
            complaint["id"],
            current_user.id,
            result.model_dump(mode="json"),
        )
    except Exception:
        raise HTTPException(status_code=503, detail="The advisory result could not be saved.") from None
    return {"review_id": saved.get("id"), "result": result, "requires_human_review": True}


@router.post("/complaints/{complaint_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_complaint_evidence(
    complaint_id: str,
    file: UploadFile = File(..., description="Evidence photograph (JPEG, PNG, WebP)"),
    notes: Optional[str] = Form(None, description="Resolution notes accompanying the photograph"),
    gps_latitude: float = Form(..., ge=-90, le=90),
    gps_longitude: float = Form(..., ge=-180, le=180),
    gps_accuracy_m: float = Form(..., gt=0, le=5000),
    current_user: AuthenticatedUser = Depends(require_roles([UserRole.DEPARTMENT_HEAD, UserRole.HOSPITAL_ADMIN, UserRole.HIGHER_AUTHORITY])),
    complaint_repo: ComplaintRepository = Depends(get_complaint_repository),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Upload resolution evidence photograph to the private 'evidence' Supabase Storage bucket.
    Validates file MIME type, enforces 5MB limit, and creates metadata in database.
    """
    # 1. Verify complaint exists
    complaint = complaint_repo.get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found."
        )

    # 2. Check department access
    check_complaint_access(current_user, complaint)

    # 3. Store file and record metadata
    result = await storage_service.upload_evidence(
        complaint_id=complaint["id"],
        file=file,
        notes=notes,
        submitted_by=current_user.id,
        gps_latitude=gps_latitude,
        gps_longitude=gps_longitude,
        gps_accuracy_m=gps_accuracy_m,
    )
    return result


@router.get("/complaints/{complaint_id}/evidence", response_model=List[EvidenceResponse])
def get_complaint_evidence(
    complaint_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    complaint_repo: ComplaintRepository = Depends(get_complaint_repository),
    evidence_repo: EvidenceRepository = Depends(get_evidence_repository),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Retrieve all evidence records for a complaint with temporary signed URLs.
    Enforces department isolation to prevent public or cross-department photo exposure.
    """
    complaint = complaint_repo.get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found."
        )

    check_complaint_access(current_user, complaint)

    items = evidence_repo.get_evidence_by_complaint(complaint["id"])
    for item in items:
        # Generate temporary signed URL (valid 1 hour)
        if item.get("file_path"):
            item["signed_url"] = storage_service.get_signed_url(item["file_path"], expires_in=3600)
    return items


@router.post("/evidence/{evidence_id}/verify", response_model=EvidenceResponse)
def verify_evidence(
    evidence_id: str,
    payload: EvidenceVerificationRequest,
    current_user: AuthenticatedUser = Depends(require_roles([UserRole.DEPARTMENT_HEAD, UserRole.HOSPITAL_ADMIN, UserRole.HIGHER_AUTHORITY])),
    evidence_repo: EvidenceRepository = Depends(get_evidence_repository),
    complaint_repo: ComplaintRepository = Depends(get_complaint_repository)
):
    """
    Verify evidence authenticity and resolution efficacy.
    Used by:
    - Evidence Verification Agent (through backend integration)
    - Department Head / Hospital Admin
    """
    evidence = evidence_repo.get_evidence_by_id(evidence_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID '{evidence_id}' not found."
        )

    # Evidence cannot be reviewed without a valid complaint association.
    complaint = complaint_repo.get_complaint_by_id(evidence["complaint_id"])
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated complaint not found.")
    check_complaint_access(current_user, complaint)

    if payload.verified and not evidence_repo.has_ai_analysis(evidence_id):
        raise HTTPException(status_code=409, detail="Run the AI evidence advisory before human verification.")
    if payload.verified and (evidence.get("gps_latitude") is None or evidence.get("gps_longitude") is None):
        raise HTTPException(status_code=409, detail="Evidence is missing its GPS position.")

    outcome = "Approved" if payload.verified else "Rejected"
    verification_note = f"{outcome}: {payload.notes or 'No remarks provided.'}"

    updated = evidence_repo.verify_evidence(
        evidence_id=evidence_id,
        verified=payload.verified,
        verified_by=current_user.id,
        notes=verification_note
    )
    return updated
