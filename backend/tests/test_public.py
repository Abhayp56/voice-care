import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_publication_service
from app.models.complaint import PublicComplaintResponse
from app.models.dashboard import PublicDepartmentStatsResponse

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()


def test_public_complaints_no_pii():
    mock_service = MagicMock()
    mock_service.get_public_complaints.return_value = ([
        PublicComplaintResponse(
            complaint_number="VC-2026-0001",
            department_name="Maintenance",
            category_name="Electricity Problem",
            status="in_progress",
            submission_date="2026-11-07"
        )
    ], 1)
    app.dependency_overrides[get_publication_service] = lambda: mock_service

    response = client.get("/api/public/complaints")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    record = data["complaints"][0]

    assert "complaint_number" in record
    assert "department_name" in record
    assert "status" in record
    assert "patient_name" not in record
    assert "patient_phone" not in record
    assert "description" not in record
    assert "assigned_to" not in record


def test_public_tracking_status_success():
    mock_service = MagicMock()
    mock_service.get_public_tracking_status.return_value = PublicComplaintResponse(
        complaint_number="VC-2026-0002",
        department_name="Sanitation",
        category_name="Washroom Cleanliness",
        status="in_progress",
        submission_date="2026-11-07"
    )
    app.dependency_overrides[get_publication_service] = lambda: mock_service

    response = client.get("/api/public/complaints/VC-2026-0002")
    assert response.status_code == 200
    assert response.json()["complaint_number"] == "VC-2026-0002"
    assert response.json()["status"] == "in_progress"


def test_public_department_stats():
    mock_service = MagicMock()
    mock_service.get_public_department_statistics.return_value = [
        PublicDepartmentStatsResponse(
            department_name="Maintenance",
            total_complaints=5,
            resolved_count=3,
            open_count=2
        ),
        PublicDepartmentStatsResponse(
            department_name="Sanitation",
            total_complaints=8,
            resolved_count=6,
            open_count=2
        )
    ]
    app.dependency_overrides[get_publication_service] = lambda: mock_service

    response = client.get("/api/public/department-statistics")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["department_name"] == "Maintenance"
    assert response.json()[0]["total_complaints"] == 5
