import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import (
    get_complaint_repository,
    get_department_repository,
    get_status_history_repository
)
from app.repositories.complaint_repository import ComplaintRepository

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()


def test_complaint_number_generation():
    mock_client = MagicMock()
    mock_res = MagicMock()
    mock_res.data = 16
    mock_client.rpc.return_value.execute.return_value = mock_res

    repo = ComplaintRepository(client=mock_client)
    complaint_num = repo.generate_next_complaint_number()
    assert complaint_num == "VC-2026-0016"
    assert mock_client.rpc.call_count == 1
    assert mock_client.rpc.call_args.args[0] == "next_complaint_number"
    assert isinstance(mock_client.rpc.call_args.args[1]["p_year"], int)


def test_status_transition_uses_atomic_history_rpc():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [{"id": "complaint-1", "status": "resolved"}]
    mock_client.rpc.return_value.execute.return_value = mock_response
    repo = ComplaintRepository(client=mock_client)

    updated = repo.update_complaint_status(
        complaint_id="complaint-1", new_status="resolved", changed_by="trusted-user"
    )

    assert updated["status"] == "resolved"
    args = mock_client.rpc.call_args.args
    assert args[0] == "transition_complaint_status"
    assert args[1]["p_changed_by"] == "trusted-user"


def test_create_complaint_endpoint_auto_routing(auth_headers_admin):
    mock_dept_repo = MagicMock()
    mock_dept_repo.get_category_by_id.return_value = {
        "id": "cat-water-001",
        "name": "Drinking Water",
        "default_priority": "high"
    }
    mock_dept_repo.get_department_for_category.return_value = "dept-sanit-002"
    mock_dept_repo.get_department_by_id.return_value = {
        "id": "dept-sanit-002",
        "name": "Sanitation"
    }

    mock_complaint_repo = MagicMock()
    mock_complaint_repo.create_complaint.return_value = {
        "id": "comp-test-123",
        "complaint_number": "VC-2026-0020",
        "patient_name": "Anita Roy",
        "patient_phone": "+91-9876500000",
        "description": "No drinking water available on 2nd floor",
        "language": "en",
        "category_id": "cat-water-001",
        "department_id": "dept-sanit-002",
        "priority": "high",
        "status": "received",
        "assigned_to": None,
        "resolved_at": None,
        "created_at": "2026-11-07T10:00:00Z",
        "updated_at": "2026-11-07T10:00:00Z",
        "department_name": "Sanitation",
        "category_name": "Drinking Water"
    }

    mock_history_repo = MagicMock()

    app.dependency_overrides[get_department_repository] = lambda: mock_dept_repo
    app.dependency_overrides[get_complaint_repository] = lambda: mock_complaint_repo
    app.dependency_overrides[get_status_history_repository] = lambda: mock_history_repo

    payload = {
        "description": "No drinking water available on 2nd floor",
        "category_id": "cat-water-001",
        "language": "en",
        "patient_name": "Anita Roy",
        "patient_phone": "+91-9876500000"
    }

    response = client.post("/api/complaints", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["complaint_number"] == "VC-2026-0020"
    assert data["department_id"] == "dept-sanit-002"
    assert data["priority"] == "high"


def test_create_complaint_ignores_caller_department_and_priority():
    mock_dept_repo = MagicMock()
    mock_dept_repo.get_category_by_id.return_value = {
        "id": "cat-water-001", "name": "Drinking Water", "default_priority": "high"
    }
    mock_dept_repo.get_department_for_category.return_value = "dept-sanit-002"
    mock_dept_repo.get_department_by_id.return_value = {"id": "dept-sanit-002", "name": "Sanitation"}
    mock_complaint_repo = MagicMock()
    mock_complaint_repo.create_complaint.return_value = {
        "id": "comp-test-124", "complaint_number": "VC-2026-0021",
        "description": "No water available", "language": "en", "category_id": "cat-water-001",
        "department_id": "dept-sanit-002", "priority": "high", "status": "received",
        "created_at": "2026-11-07T10:00:00Z", "updated_at": "2026-11-07T10:00:00Z"
    }
    mock_history_repo = MagicMock()
    app.dependency_overrides[get_department_repository] = lambda: mock_dept_repo
    app.dependency_overrides[get_complaint_repository] = lambda: mock_complaint_repo
    app.dependency_overrides[get_status_history_repository] = lambda: mock_history_repo

    response = client.post("/api/complaints", json={
        "description": "No water available", "category_id": "cat-water-001",
        "department_id": "dept-maint-001", "priority": "critical"
    })
    assert response.status_code == 201
    kwargs = mock_complaint_repo.create_complaint.call_args.kwargs
    assert kwargs["department_id"] == "dept-sanit-002"
    assert kwargs["priority"] == "high"


def test_create_complaint_invalid_category():
    mock_dept_repo = MagicMock()
    mock_dept_repo.get_category_by_id.return_value = None

    app.dependency_overrides[get_department_repository] = lambda: mock_dept_repo

    payload = {
        "description": "Test invalid category complaint",
        "category_id": "non-existent-cat"
    }

    response = client.post("/api/complaints", json=payload)
    assert response.status_code == 400
    assert "Invalid category_id" in response.json()["detail"]


def test_get_complaint_by_id_success(auth_headers_admin):
    mock_complaint_repo = MagicMock()
    mock_complaint_repo.get_complaint_by_id.return_value = {
        "id": "comp-uuid-001",
        "complaint_number": "VC-2026-0001",
        "description": "Power socket sparks",
        "language": "en",
        "category_id": "cat-power-002",
        "department_id": "dept-maint-001",
        "priority": "medium",
        "status": "received",
        "created_at": "2026-11-07T08:00:00Z",
        "updated_at": "2026-11-07T08:00:00Z"
    }

    app.dependency_overrides[get_complaint_repository] = lambda: mock_complaint_repo

    response = client.get("/api/complaints/VC-2026-0001", headers=auth_headers_admin)
    assert response.status_code == 200
    assert response.json()["complaint_number"] == "VC-2026-0001"


def test_get_complaint_not_found(auth_headers_admin):
    mock_complaint_repo = MagicMock()
    mock_complaint_repo.get_complaint_by_id.return_value = None

    app.dependency_overrides[get_complaint_repository] = lambda: mock_complaint_repo

    response = client.get("/api/complaints/VC-2026-9999", headers=auth_headers_admin)
    assert response.status_code == 404


def test_update_complaint_status(auth_headers_admin):
    mock_complaint_repo = MagicMock()
    mock_complaint_repo.get_complaint_by_id.side_effect = [
        {
            "id": "comp-uuid-001",
            "complaint_number": "VC-2026-0001",
            "description": "Power socket sparks",
            "language": "en",
            "category_id": "cat-power-002",
            "department_id": "dept-maint-001",
            "priority": "medium",
            "status": "in_progress",
            "created_at": "2026-11-07T08:00:00Z",
            "updated_at": "2026-11-07T08:00:00Z"
        },
        {
            "id": "comp-uuid-001",
            "complaint_number": "VC-2026-0001",
            "description": "Power socket sparks",
            "language": "en",
            "category_id": "cat-power-002",
            "department_id": "dept-maint-001",
            "priority": "medium",
            "status": "resolved",
            "created_at": "2026-11-07T08:00:00Z",
            "updated_at": "2026-11-07T08:00:00Z"
        }
    ]
    mock_complaint_repo.update_complaint_status.return_value = {
        "id": "comp-uuid-001",
        "status": "resolved"
    }

    app.dependency_overrides[get_complaint_repository] = lambda: mock_complaint_repo

    payload = {
        "status": "resolved",
        "note": "Replaced faulty switch board."
    }

    response = client.patch(
        "/api/complaints/comp-uuid-001/status",
        json=payload,
        headers=auth_headers_admin
    )
    assert response.status_code == 200


def test_department_staff_cannot_resolve_or_choose_audit_identity(auth_headers_maintenance_staff):
    mock_complaint_repo = MagicMock()
    mock_complaint_repo.get_complaint_by_id.return_value = {
        "id": "comp-uuid-001", "complaint_number": "VC-2026-0001",
        "department_id": "dept-maint-001", "status": "in_progress"
    }
    app.dependency_overrides[get_complaint_repository] = lambda: mock_complaint_repo

    response = client.patch(
        "/api/complaints/comp-uuid-001/status",
        json={"status": "resolved", "changed_by": "some-other-user"},
        headers=auth_headers_maintenance_staff,
    )

    assert response.status_code == 403
    mock_complaint_repo.update_complaint_status.assert_not_called()


def test_status_history_identity_comes_from_authenticated_user(auth_headers_admin):
    mock_complaint_repo = MagicMock()
    complaint = {
        "id": "comp-uuid-001", "complaint_number": "VC-2026-0001",
        "department_id": "dept-maint-001", "status": "in_progress"
    }
    mock_complaint_repo.get_complaint_by_id.side_effect = [complaint, {**complaint, "status": "resolved"}]
    mock_complaint_repo.update_complaint_status.return_value = {"id": "comp-uuid-001", "status": "resolved"}
    app.dependency_overrides[get_complaint_repository] = lambda: mock_complaint_repo

    response = client.patch(
        "/api/complaints/comp-uuid-001/status",
        json={"status": "resolved", "changed_by": "forged-user"},
        headers=auth_headers_admin,
    )

    assert response.status_code == 200
    assert mock_complaint_repo.update_complaint_status.call_args.kwargs["changed_by"] == "admin-user-001"
