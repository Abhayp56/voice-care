import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_department_repository, get_complaint_repository

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()


def test_list_departments():
    mock_repo = MagicMock()
    mock_repo.get_all_departments.return_value = [
        {"id": "dept-1", "name": "Maintenance", "description": "Infra", "created_at": "2026-11-07T00:00:00Z", "updated_at": "2026-11-07T00:00:00Z"},
        {"id": "dept-2", "name": "Sanitation", "description": "Cleanliness", "created_at": "2026-11-07T00:00:00Z", "updated_at": "2026-11-07T00:00:00Z"}
    ]
    app.dependency_overrides[get_department_repository] = lambda: mock_repo

    response = client.get("/api/departments")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_department_isolation_forbidden(auth_headers_sanitation_staff):
    mock_dept_repo = MagicMock()
    mock_dept_repo.get_department_by_id.return_value = {
        "id": "dept-maint-001",
        "name": "Maintenance"
    }
    app.dependency_overrides[get_department_repository] = lambda: mock_dept_repo

    response = client.get(
        "/api/departments/dept-maint-001/complaints",
        headers=auth_headers_sanitation_staff
    )
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


def test_department_isolation_allowed_for_own_department(auth_headers_maintenance_staff):
    mock_dept_repo = MagicMock()
    mock_dept_repo.get_department_by_id.return_value = {
        "id": "dept-maint-001",
        "name": "Maintenance"
    }

    mock_complaint_repo = MagicMock()
    mock_complaint_repo.get_complaints_by_department.return_value = ([
        {"id": "c1", "complaint_number": "VC-2026-0001", "department_id": "dept-maint-001"}
    ], 1)

    app.dependency_overrides[get_department_repository] = lambda: mock_dept_repo
    app.dependency_overrides[get_complaint_repository] = lambda: mock_complaint_repo

    response = client.get(
        "/api/departments/dept-maint-001/complaints",
        headers=auth_headers_maintenance_staff
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_department_isolation_admin_override(auth_headers_admin):
    mock_dept_repo = MagicMock()
    mock_dept_repo.get_department_by_id.return_value = {
        "id": "dept-maint-001",
        "name": "Maintenance"
    }

    mock_complaint_repo = MagicMock()
    mock_complaint_repo.get_complaints_by_department.return_value = ([], 0)

    app.dependency_overrides[get_department_repository] = lambda: mock_dept_repo
    app.dependency_overrides[get_complaint_repository] = lambda: mock_complaint_repo

    response = client.get(
        "/api/departments/dept-maint-001/complaints",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
