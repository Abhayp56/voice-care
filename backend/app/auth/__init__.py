"""Authentication and authorization package."""
from app.auth.authentication import get_current_user, get_optional_current_user
from app.auth.permissions import require_roles, check_department_access

__all__ = [
    "get_current_user",
    "get_optional_current_user",
    "require_roles",
    "check_department_access",
]

