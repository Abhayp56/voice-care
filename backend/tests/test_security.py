import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from app.auth import authentication
from app.config import Settings, settings
from app.models.complaint import ComplaintCreate, ComplaintStatusUpdate
from app.models.evidence import EvidenceVerificationRequest
from app.models.user import AuthenticatedUser, UserRole
from app.auth.permissions import check_department_access, require_roles
from app.routes.complaints import create_complaint, update_complaint_status
from app.routes.dashboard import get_dashboard_statistics
from app.routes.evidence import verify_evidence
from app.main import app


def run_dependency(coroutine):
    """Run these async dependencies directly; they deliberately contain no await points."""
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value


def test_invalid_bearer_token_is_rejected(monkeypatch):
    mock_client = MagicMock()
    mock_client.auth.get_user.side_effect = RuntimeError("invalid token")
    monkeypatch.setattr(authentication, "get_supabase_client", lambda: mock_client)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-test-token")
    with pytest.raises(HTTPException) as exc:
        run_dependency(authentication.get_current_user(credentials=credentials, user_repo=MagicMock()))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Authentication failed."


def test_optional_auth_does_not_downgrade_invalid_token_to_anonymous(monkeypatch):
    mock_client = MagicMock()
    mock_client.auth.get_user.side_effect = RuntimeError("invalid token")
    monkeypatch.setattr(authentication, "get_supabase_client", lambda: mock_client)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-test-token")
    with pytest.raises(HTTPException) as exc:
        run_dependency(authentication.get_optional_current_user(credentials=credentials, user_repo=MagicMock()))
    assert exc.value.status_code == 401


def test_missing_authentication_is_rejected():
    with pytest.raises(HTTPException) as exc:
        run_dependency(authentication.get_current_user(credentials=None, user_repo=MagicMock()))
    assert exc.value.status_code == 401


def test_production_rejects_development_identity_headers(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    # Even a mistaken true setting cannot activate identity headers in production.
    monkeypatch.setattr(settings, "ALLOW_DEV_AUTH_HEADERS", True)
    with pytest.raises(HTTPException) as exc:
        run_dependency(authentication.get_current_user(
            credentials=None,
            x_user_id="attacker-id", x_user_role="hospital_admin",
            x_department_id="attacker-department", user_repo=MagicMock(),
        ))
    assert exc.value.status_code == 401


def test_development_headers_require_explicit_opt_in(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ALLOW_DEV_AUTH_HEADERS", False)
    with pytest.raises(HTTPException) as exc:
        run_dependency(authentication.get_current_user(
            credentials=None, x_user_id="local-user", x_user_role="hospital_admin", user_repo=MagicMock()
        ))
    assert exc.value.status_code == 401

    monkeypatch.setattr(settings, "ALLOW_DEV_AUTH_HEADERS", True)
    user = run_dependency(authentication.get_current_user(
        credentials=None, x_user_id="local-user", x_user_role="department_staff",
        x_department_id="dept-local", user_repo=MagicMock(),
    ))
    assert user.id == "local-user"
    assert user.role == UserRole.DEPARTMENT_STAFF
    assert user.department_id == "dept-local"


def test_bearer_role_and_department_come_from_database_profile(monkeypatch):
    mock_client = MagicMock()
    mock_client.auth.get_user.return_value = SimpleNamespace(
        user=SimpleNamespace(id="trusted-user", email="staff@example.invalid", user_metadata={})
    )
    monkeypatch.setattr(authentication, "get_supabase_client", lambda: mock_client)
    user_repo = MagicMock()
    user_repo.get_profile_by_id.return_value = {
        "id": "trusted-user", "role": "department_staff", "department_id": "trusted-department"
    }
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-test-token")
    user = run_dependency(authentication.get_current_user(
        credentials=credentials,
        x_user_id="attacker-id", x_user_role="hospital_admin",
        x_department_id="attacker-department", user_repo=user_repo,
    ))
    assert user.role == UserRole.DEPARTMENT_STAFF
    assert user.department_id == "trusted-department"
    user_repo.get_profile_by_id.assert_called_once_with("trusted-user")


def test_verified_bearer_without_trusted_profile_is_rejected(monkeypatch):
    mock_client = MagicMock()
    mock_client.auth.get_user.return_value = SimpleNamespace(
        user=SimpleNamespace(id="unprovisioned-user", email="user@example.invalid", user_metadata={})
    )
    monkeypatch.setattr(authentication, "get_supabase_client", lambda: mock_client)
    user_repo = MagicMock()
    user_repo.get_profile_by_id.return_value = None
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-test-token")
    with pytest.raises(HTTPException) as exc:
        run_dependency(authentication.get_current_user(credentials=credentials, user_repo=user_repo))
    assert exc.value.status_code == 403


def test_cors_uses_explicit_configured_origins():
    cors = next(middleware for middleware in app.user_middleware if middleware.cls.__name__ == "CORSMiddleware")
    assert cors.kwargs["allow_origins"] == settings.ALLOWED_ORIGINS
    assert "*" not in cors.kwargs["allow_origins"]
    assert cors.kwargs["allow_credentials"] is True


def test_production_settings_reject_dev_auth_and_wildcard_cors():
    common = {
        "SUPABASE_URL": "https://test-project.invalid",
        "SUPABASE_ANON_KEY": "test-anon-placeholder",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-placeholder",
        "ENVIRONMENT": "production",
    }
    with pytest.raises(ValidationError):
        Settings(**common, ALLOW_DEV_AUTH_HEADERS=True)
    with pytest.raises(ValidationError):
        Settings(**{**common, "ENVIRONMENT": " Production "}, ALLOW_DEV_AUTH_HEADERS=True)
    with pytest.raises(ValidationError):
        Settings(**common, ALLOWED_ORIGINS=["*"])
    with pytest.raises(ValidationError):
        Settings(**common, ALLOWED_ORIGINS=[])


def test_department_isolation_rejects_cross_department_access():
    user = AuthenticatedUser(id="staff-1", role=UserRole.DEPARTMENT_STAFF, department_id="dept-a")
    with pytest.raises(HTTPException) as exc:
        check_department_access(user, "dept-b")
    assert exc.value.status_code == 403


def test_department_staff_cannot_resolve_and_cannot_forge_actor():
    complaint_repo = MagicMock()
    complaint_repo.get_complaint_by_id.return_value = {"id": "c1", "department_id": "dept-a"}
    staff = AuthenticatedUser(id="verified-staff", role=UserRole.DEPARTMENT_STAFF, department_id="dept-a")
    with pytest.raises(HTTPException) as exc:
        update_complaint_status(
            complaint_id="c1",
            payload=ComplaintStatusUpdate.model_validate({"status": "resolved", "changed_by": "forged-user"}),
            current_user=staff,
            complaint_repo=complaint_repo,
        )
    assert exc.value.status_code == 403
    complaint_repo.update_complaint_status.assert_not_called()


def test_public_complaint_creation_uses_server_routing_and_priority():
    department_repo = MagicMock()
    department_repo.get_category_by_id.return_value = {
        "id": "cat-water", "name": "Drinking Water", "default_priority": "high"
    }
    department_repo.get_department_for_category.return_value = "trusted-department"
    department_repo.get_department_by_id.return_value = {"id": "trusted-department", "name": "Sanitation"}
    complaint_repo = MagicMock()
    complaint_repo.create_complaint.return_value = {
        "id": "c1", "complaint_number": "VC-2026-0001", "description": "No drinking water",
        "language": "en", "category_id": "cat-water", "department_id": "trusted-department",
        "priority": "high", "status": "received", "created_at": "2026-11-07T12:00:00Z",
        "updated_at": "2026-11-07T12:00:00Z"
    }
    result = create_complaint(
        payload=ComplaintCreate.model_validate({
            "description": "No drinking water", "category_id": "cat-water",
            "department_id": "attacker-department", "priority": "critical"
        }),
        complaint_repo=complaint_repo,
        dept_repo=department_repo,
        history_repo=MagicMock(),
    )
    assert result["department_id"] == "trusted-department"
    assert complaint_repo.create_complaint.call_args.kwargs["priority"] == "high"


def test_department_dashboard_cannot_return_all_department_metrics():
    staff_without_department = AuthenticatedUser(id="staff-1", role=UserRole.DEPARTMENT_STAFF)
    service = MagicMock()
    with pytest.raises(HTTPException) as exc:
        get_dashboard_statistics(current_user=staff_without_department, service=service)
    assert exc.value.status_code == 403
    service.get_dashboard_statistics.assert_not_called()


def test_resolved_status_audit_identity_comes_from_authenticated_user():
    complaint_repo = MagicMock()
    complaint = {"id": "c1", "department_id": "dept-a", "status": "in_progress"}
    complaint_repo.get_complaint_by_id.side_effect = [complaint, {**complaint, "status": "resolved"}]
    complaint_repo.update_complaint_status.return_value = {"id": "c1", "status": "resolved"}
    admin = AuthenticatedUser(id="trusted-admin", role=UserRole.HOSPITAL_ADMIN)

    result = update_complaint_status(
        complaint_id="c1",
        payload=ComplaintStatusUpdate.model_validate({"status": "resolved", "changed_by": "forged-user"}),
        current_user=admin,
        complaint_repo=complaint_repo,
    )

    assert result["status"] == "resolved"
    assert complaint_repo.update_complaint_status.call_args.kwargs["changed_by"] == "trusted-admin"


def test_only_human_reviewer_can_verify_and_actor_is_authenticated_user():
    evidence_repo = MagicMock()
    evidence_repo.get_evidence_by_id.return_value = {"id": "e1", "complaint_id": "c1"}
    evidence_repo.verify_evidence.return_value = {
        "id": "e1", "complaint_id": "c1", "file_path": "c1/a.jpg", "file_type": "image",
        "created_at": "2026-11-07T12:00:00Z", "verified_by": "head-1", "verified_at": "2026-11-07T12:05:00Z"
    }
    complaint_repo = MagicMock()
    complaint_repo.get_complaint_by_id.return_value = {"id": "c1", "department_id": "dept-a"}
    staff = AuthenticatedUser(id="staff-1", role=UserRole.DEPARTMENT_STAFF, department_id="dept-a")
    with pytest.raises(HTTPException) as exc:
        require_roles([UserRole.DEPARTMENT_HEAD, UserRole.HOSPITAL_ADMIN])(current_user=staff)
    assert exc.value.status_code == 403

    reviewer = AuthenticatedUser(id="head-1", role=UserRole.DEPARTMENT_HEAD, department_id="dept-a")
    result = verify_evidence(
        evidence_id="e1",
        payload=EvidenceVerificationRequest.model_validate({"verified": True, "verified_by": "forged-user"}),
        current_user=reviewer,
        evidence_repo=evidence_repo,
        complaint_repo=complaint_repo,
    )
    assert result["verified_by"] == "head-1"
    assert evidence_repo.verify_evidence.call_args.kwargs["verified_by"] == "head-1"

    evidence_repo.reset_mock()
    evidence_repo.get_evidence_by_id.return_value = {"id": "e1", "complaint_id": "c1"}
    evidence_repo.verify_evidence.return_value = {
        "id": "e1", "complaint_id": "c1", "file_path": "c1/a.jpg", "file_type": "image",
        "created_at": "2026-11-07T12:00:00Z", "verified_by": "head-1", "verified_at": None
    }
    rejected = verify_evidence(
        evidence_id="e1", payload=EvidenceVerificationRequest(verified=False, notes="Not sufficient."),
        current_user=reviewer, evidence_repo=evidence_repo, complaint_repo=complaint_repo,
    )
    assert rejected["verified_at"] is None
    assert evidence_repo.verify_evidence.call_args.kwargs["verified"] is False
    assert evidence_repo.verify_evidence.call_args.kwargs["notes"].startswith("Rejected:")


def test_tracked_environment_examples_contain_placeholders_only():
    root = Path(__file__).resolve().parents[2]
    example = (root / ".env.example").read_text(encoding="utf-8") if (root / ".env.example").exists() else ""
    example += (root / "backend" / ".env.example").read_text(encoding="utf-8")
    readme = (root / "backend" / "README.md").read_text(encoding="utf-8")
    token_pattern = re.compile(r"eyJ[A-Za-z0-9_-]{18,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}")

    assert token_pattern.search(example) is None
    assert "replace-with-supabase-anon-key" in example
    assert "replace-with-rotated-service-role-key" in example
    assert token_pattern.search(readme) is None
