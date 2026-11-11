import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app
from app.models.user import AuthenticatedUser, UserRole
from app.auth.permissions import check_department_access, require_roles

client = TestClient(app)


def test_missing_auth_header_fails():
    """Accessing protected complaint route without auth returns 401."""
    response = client.get("/api/complaints/comp-123")
    assert response.status_code == 401
    assert "Missing authentication credentials" in response.json()["detail"]


def test_check_department_access_admin_allowed():
    admin = AuthenticatedUser(
        id="u-admin",
        role=UserRole.HOSPITAL_ADMIN,
        department_id=None
    )
    # Admin should not raise exception for any department
    check_department_access(admin, "any-dept-id")


def test_check_department_access_staff_same_department():
    staff = AuthenticatedUser(
        id="u-staff",
        role=UserRole.DEPARTMENT_STAFF,
        department_id="dept-1"
    )
    # Matching department should succeed
    check_department_access(staff, "dept-1")


def test_check_department_access_staff_different_department():
    staff = AuthenticatedUser(
        id="u-staff",
        role=UserRole.DEPARTMENT_STAFF,
        department_id="dept-1"
    )
    # Different department raises 403
    with pytest.raises(HTTPException) as exc_info:
        check_department_access(staff, "dept-2")
    assert exc_info.value.status_code == 403


def test_require_roles_checker():
    checker = require_roles([UserRole.HOSPITAL_ADMIN, UserRole.DEPARTMENT_HEAD])
    admin = AuthenticatedUser(id="u1", role=UserRole.HOSPITAL_ADMIN)
    staff = AuthenticatedUser(id="u2", role=UserRole.DEPARTMENT_STAFF)

    # Admin passes
    assert checker(admin) == admin

    # Staff is rejected with 403
    with pytest.raises(HTTPException) as exc_info:
        checker(staff)
    assert exc_info.value.status_code == 403

