import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.services.dashboard_service import DashboardService
from app.dependencies import get_dashboard_service
from app.auth.authentication import get_current_user
from app.models.dashboard import DashboardStatsResponse
from app.models.user import AuthenticatedUser, UserRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_statistics(
    department_id: Optional[str] = Query(None, description="Filter stats by department UUID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get aggregated operational statistics.
    Calculates live metrics from actual database records:
    - Total, pending, in-progress, resolved, escalated, and overdue counts.
    - Category, department, priority distributions.
    - Average resolution time.
    
    Department Isolation:
    - Department staff and heads will automatically see stats restricted to their assigned department.
    """
    effective_dept_id = department_id
    if current_user.role in [UserRole.DEPARTMENT_STAFF, UserRole.DEPARTMENT_HEAD]:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User profile has no assigned department.")
        if department_id and department_id != current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden for another department.")
        effective_dept_id = current_user.department_id

    stats = service.get_dashboard_statistics(department_id=effective_dept_id)
    return stats
