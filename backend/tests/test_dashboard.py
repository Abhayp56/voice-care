import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_dashboard_service
from app.services.dashboard_service import DashboardService
from app.models.dashboard import DashboardStatsResponse

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()


def test_dashboard_service_calculations():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.data = [
        {
            "id": "c1",
            "status": "received",
            "priority": "high",
            "department_id": "d1",
            "category_id": "cat1",
            "created_at": "2026-11-07T00:00:00Z",
            "resolved_at": None,
            "departments": {"name": "Maintenance"},
            "complaint_categories": {"name": "Electricity"}
        },
        {
            "id": "c2",
            "status": "resolved",
            "priority": "medium",
            "department_id": "d1",
            "category_id": "cat1",
            "created_at": "2026-11-06T10:00:00Z",
            "resolved_at": "2026-11-06T12:30:00Z",
            "departments": {"name": "Maintenance"},
            "complaint_categories": {"name": "Electricity"}
        }
    ]
    mock_client.table.return_value.select.return_value.execute.return_value = mock_resp

    service = DashboardService(client=mock_client)
    stats = service.get_dashboard_statistics()

    assert stats.total_complaints == 2
    assert stats.pending_complaints == 1
    assert stats.resolved_complaints == 1
    assert stats.average_resolution_hours == 2.5


def test_dashboard_stats_endpoint(auth_headers_admin):
    mock_service = MagicMock()
    mock_service.get_dashboard_statistics.return_value = DashboardStatsResponse(
        total_complaints=10,
        pending_complaints=4,
        in_progress_complaints=2,
        resolved_complaints=3,
        escalated_complaints=1,
        overdue_complaints=2,
        average_resolution_hours=3.2
    )
    app.dependency_overrides[get_dashboard_service] = lambda: mock_service

    response = client.get("/api/dashboard/stats", headers=auth_headers_admin)
    assert response.status_code == 200
    data = response.json()
    assert data["total_complaints"] == 10
    assert data["pending_complaints"] == 4
    assert data["resolved_complaints"] == 3


def test_department_dashboard_cannot_request_another_department(auth_headers_maintenance_staff):
    mock_service = MagicMock()
    app.dependency_overrides[get_dashboard_service] = lambda: mock_service
    response = client.get(
        "/api/dashboard/stats?department_id=dept-sanit-002",
        headers=auth_headers_maintenance_staff,
    )
    assert response.status_code == 403
    mock_service.get_dashboard_statistics.assert_not_called()
