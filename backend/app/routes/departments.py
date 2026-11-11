import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.repositories.department_repository import DepartmentRepository
from app.repositories.complaint_repository import ComplaintRepository
from app.dependencies import get_department_repository, get_complaint_repository
from app.auth.authentication import get_current_user
from app.auth.permissions import check_department_access
from app.models.department import (
    DepartmentResponse,
    ComplaintCategoryResponse,
    DepartmentMappingResponse,
)
from app.models.user import AuthenticatedUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Departments & Categories"])


@router.get("/departments", response_model=List[DepartmentResponse])
def get_departments(
    repo: DepartmentRepository = Depends(get_department_repository)
):
    """Retrieve all hospital departments."""
    return repo.get_all_departments()


@router.get("/departments/{department_id}", response_model=DepartmentResponse)
def get_department_by_id(
    department_id: str,
    repo: DepartmentRepository = Depends(get_department_repository)
):
    """Retrieve a department by UUID."""
    dept = repo.get_department_by_id(department_id)
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID '{department_id}' not found."
        )
    return dept


@router.get("/departments/{department_id}/complaints")
def get_department_complaints(
    department_id: str,
    status: Optional[str] = Query(None, description="Filter by status (e.g. received, in_progress)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    dept_repo: DepartmentRepository = Depends(get_department_repository),
    complaint_repo: ComplaintRepository = Depends(get_complaint_repository)
):
    """
    Retrieve all complaints assigned to a specific department.
    Enforces department isolation: staff from other departments cannot view this data.
    """
    # 1. Verify target department exists
    dept = dept_repo.get_department_by_id(department_id)
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID '{department_id}' not found."
        )

    # 2. Enforce department isolation check
    check_department_access(current_user, department_id)

    # 3. Retrieve paginated complaints
    complaints, total = complaint_repo.get_complaints_by_department(
        department_id=department_id,
        status=status,
        limit=limit,
        offset=offset
    )
    return {
        "department_id": department_id,
        "department_name": dept["name"],
        "total": total,
        "limit": limit,
        "offset": offset,
        "complaints": complaints
    }


@router.get("/categories", response_model=List[ComplaintCategoryResponse])
def get_categories(
    repo: DepartmentRepository = Depends(get_department_repository)
):
    """Retrieve all complaint categories with default SLA priorities."""
    return repo.get_all_categories()


@router.get("/categories/{category_id}/department")
def get_routed_department_for_category(
    category_id: str,
    repo: DepartmentRepository = Depends(get_department_repository)
):
    """
    Helper for AI Orchestrator:
    Find the mapped department for a given complaint category.
    """
    dept_id = repo.get_department_for_category(category_id)
    if not dept_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No department mapping found for category '{category_id}'."
        )
    dept = repo.get_department_by_id(dept_id)
    return {
        "category_id": category_id,
        "department_id": dept_id,
        "department_name": dept["name"] if dept else None
    }


@router.get("/department-mappings", response_model=List[DepartmentMappingResponse])
def get_all_mappings(
    repo: DepartmentRepository = Depends(get_department_repository)
):
    """Retrieve all category-to-department routing rules."""
    return repo.get_all_mappings()
