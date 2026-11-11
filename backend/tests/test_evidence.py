import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app
from app.dependencies import get_complaint_repository, get_storage_service, get_evidence_repository
from app.services.storage_service import StorageService

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()


def test_storage_validation_file_size_exceeded():
    service = StorageService(client=MagicMock())
    with pytest.raises(HTTPException) as exc_info:
        service.validate_file(
            filename="big_evidence.jpg",
            content_type="image/jpeg",
            file_size=6 * 1024 * 1024  # 6 MB
        )
    assert exc_info.value.status_code == 413


def test_storage_validation_invalid_mime_type():
    service = StorageService(client=MagicMock())
    with pytest.raises(HTTPException) as exc_info:
        service.validate_file(
            filename="malicious.exe",
            content_type="application/x-msdownload",
            file_size=1024
        )
    assert exc_info.value.status_code == 400


def test_storage_validation_rejects_mismatched_image_signature():
    service = StorageService(client=MagicMock())
    with pytest.raises(HTTPException) as exc_info:
        service.validate_file("fake.jpg", "image/jpeg", 8, content=b"GIF89a!!")
    assert exc_info.value.status_code == 400


def test_upload_evidence_endpoint(auth_headers_admin):
    mock_complaint_repo = MagicMock()
    mock_complaint_repo.get_complaint_by_id.return_value = {
        "id": "comp-123",
        "complaint_number": "VC-2026-0001",
        "department_id": "dept-1"
    }

    mock_storage_service = MagicMock()
    async def async_upload(*args, **kwargs):
        return {
            "id": "ev-001",
            "complaint_id": "comp-123",
            "file_path": "comp-123/safe.jpg",
            "file_type": "image",
            "notes": "Fixed leaking pipe",
            "submitted_by": "admin-user-001",
            "created_at": "2026-11-07T12:00:00Z",
            "signed_url": "https://kxmhrmgssjfpbsjbwlmi.supabase.co/storage/v1/object/sign/evidence/test.jpg"
        }
    mock_storage_service.upload_evidence.side_effect = async_upload

    app.dependency_overrides[get_complaint_repository] = lambda: mock_complaint_repo
    app.dependency_overrides[get_storage_service] = lambda: mock_storage_service

    files = {"file": ("test.jpg", b"fake image bytes", "image/jpeg")}
    data = {"notes": "Fixed leaking pipe"}

    response = client.post(
        "/api/complaints/comp-123/evidence",
        files=files,
        data=data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    assert response.json()["id"] == "ev-001"
    assert "signed_url" in response.json()


def test_department_staff_cannot_verify_evidence(auth_headers_maintenance_staff):
    evidence_repo = MagicMock()
    complaint_repo = MagicMock()
    app.dependency_overrides[get_evidence_repository] = lambda: evidence_repo
    app.dependency_overrides[get_complaint_repository] = lambda: complaint_repo
    response = client.post(
        "/api/evidence/evidence-1/verify",
        json={"verified": True},
        headers=auth_headers_maintenance_staff,
    )
    assert response.status_code == 403
    evidence_repo.get_evidence_by_id.assert_not_called()


def test_human_reviewer_identity_is_server_derived(auth_headers_department_head):
    evidence_repo = MagicMock()
    evidence_repo.get_evidence_by_id.return_value = {"id": "evidence-1", "complaint_id": "comp-1"}
    evidence_repo.verify_evidence.return_value = {
        "id": "evidence-1", "complaint_id": "comp-1", "file_path": "comp-1/test.jpg",
        "file_type": "image", "created_at": "2026-11-07T12:00:00Z", "verified_by": "head-user-001",
        "verified_at": "2026-11-07T12:05:00Z"
    }
    complaint_repo = MagicMock()
    complaint_repo.get_complaint_by_id.return_value = {"id": "comp-1", "department_id": "dept-maint-001"}
    app.dependency_overrides[get_evidence_repository] = lambda: evidence_repo
    app.dependency_overrides[get_complaint_repository] = lambda: complaint_repo

    response = client.post(
        "/api/evidence/evidence-1/verify",
        json={"verified": True, "verified_by": "forged-user", "notes": "Reviewed"},
        headers=auth_headers_department_head,
    )

    assert response.status_code == 200
    assert evidence_repo.verify_evidence.call_args.kwargs["verified_by"] == "head-user-001"


def test_rejected_evidence_is_not_recorded_as_approved(auth_headers_department_head):
    evidence_repo = MagicMock()
    evidence_repo.get_evidence_by_id.return_value = {"id": "evidence-1", "complaint_id": "comp-1"}
    evidence_repo.verify_evidence.return_value = {
        "id": "evidence-1", "complaint_id": "comp-1", "file_path": "comp-1/test.jpg",
        "file_type": "image", "created_at": "2026-11-07T12:00:00Z", "verified_by": "head-user-001",
        "verified_at": None, "notes": "Rejected: Photo does not show the repair."
    }
    complaint_repo = MagicMock()
    complaint_repo.get_complaint_by_id.return_value = {"id": "comp-1", "department_id": "dept-maint-001"}
    app.dependency_overrides[get_evidence_repository] = lambda: evidence_repo
    app.dependency_overrides[get_complaint_repository] = lambda: complaint_repo

    response = client.post(
        "/api/evidence/evidence-1/verify",
        json={"verified": False, "notes": "Photo does not show the repair."},
        headers=auth_headers_department_head,
    )

    assert response.status_code == 200
    assert evidence_repo.verify_evidence.call_args.kwargs["verified"] is False
    assert response.json()["verified_at"] is None
