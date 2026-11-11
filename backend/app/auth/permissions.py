import logging
from typing import List, Callable, Dict, Any
from fastapi import Depends, HTTPException, status
from app.auth.authentication import get_current_user
from app.models.user import AuthenticatedUser, UserRole
from app.services.complaint_deadlines import is_higher_authority_case

logger = logging.getLogger(__name__)


def require_roles(allowed_roles: List[UserRole]) -> Callable:
    """
    Dependency factory ensuring the current user holds one of the authorized roles.
    """
    def role_checker(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"User {current_user.id} with role '{current_user.role}' attempted unauthorized action requiring {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of the following roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


def check_department_access(user: AuthenticatedUser, department_id: str) -> None:
    """
    Enforces Department Isolation:
    - hospital_admin & higher_authority: Can access data across all hospital departments.
    - department_head & department_staff: Can ONLY access data for their assigned department_id.
    """
    # Admins and higher authorities have global oversight
    if user.role in [UserRole.HOSPITAL_ADMIN, UserRole.HIGHER_AUTHORITY]:
        return

    # Department staff and heads must match the target department
    if not user.department_id or user.department_id != department_id:
        logger.warning(
            f"Department isolation check failed: User {user.id} (Dept: {user.department_id}) "
            f"attempted to access Department {department_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You are not authorized to view or modify records for this department.",
        )


def check_complaint_access(user: AuthenticatedUser, complaint: Dict[str, Any]) -> None:
    """
    Ensures user is permitted to view or operate on the specific complaint record.
    """
    dept_id = complaint.get("department_id")
    if not dept_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Complaint has no assigned department.")
    if user.role == UserRole.HIGHER_AUTHORITY and not is_higher_authority_case(complaint):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No higher-authority review is pending for this complaint.")
    check_department_access(user, dept_id)


def check_status_update_permission(user: AuthenticatedUser, new_status: str) -> None:
    """Enforce which human roles may perform each lifecycle transition."""
    if user.role == UserRole.HIGHER_AUTHORITY:
        if new_status not in {"in_progress", "needs_review", "resolved"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Higher authority may send an overdue complaint back for action or submit its verified resolution.")
        return
    if user.role == UserRole.DEPARTMENT_HEAD:
        if new_status == "escalated":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only a hospital administrator may escalate a complaint.",
            )
    elif user.role != UserRole.HOSPITAL_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role is not authorized to update complaints.")

