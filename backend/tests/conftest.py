import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Test-only values keep imports and test clients isolated from the user's environment.
os.environ.update({
    "SUPABASE_URL": "https://test-project.invalid",
    "SUPABASE_ANON_KEY": "test-anon-placeholder",
    "SUPABASE_SERVICE_ROLE_KEY": "test-service-placeholder",
    "ENVIRONMENT": "development",
    "ALLOW_DEV_AUTH_HEADERS": "true",
    "ALLOWED_ORIGINS": '["http://localhost:3001"]',
})

from app.main import app
from app.models.user import UserRole
from app.dependencies import (
    get_complaint_repository,
    get_department_repository,
    get_dashboard_service,
    get_evidence_repository,
    get_publication_service,
    get_status_history_repository,
    get_storage_service,
    get_user_repository,
)


@pytest.fixture(autouse=True)
def mock_supabase_health_on_startup():
    """Prevent tests from attempting network calls during FastAPI lifespan startup."""
    with patch("app.main.check_supabase_connection") as mock_health:
        mock_health.return_value = {
            "status": "connected",
            "database": "reachable",
            "url": "https://test-project.invalid"
        }
        yield mock_health


@pytest.fixture(autouse=True)
def isolate_database_dependencies():
    """Ensure route tests never instantiate a live Supabase client."""
    dependencies = (
        get_complaint_repository,
        get_department_repository,
        get_dashboard_service,
        get_evidence_repository,
        get_publication_service,
        get_status_history_repository,
        get_storage_service,
        get_user_repository,
    )
    for dependency in dependencies:
        app.dependency_overrides[dependency] = lambda: MagicMock()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_supabase():
    """Mock Supabase client providing predefined table responses."""
    mock_client = MagicMock()

    mock_departments = [
        {"id": "dept-maint-001", "name": "Maintenance", "description": "Electricity, plumbing"},
        {"id": "dept-sanit-002", "name": "Sanitation", "description": "Cleanliness, washrooms"}
    ]
    mock_categories = [
        {"id": "cat-water-001", "name": "Drinking Water", "default_priority": "high"},
        {"id": "cat-power-002", "name": "Electricity Problem", "default_priority": "medium"}
    ]
    mock_mappings = [
        {"id": "map-001", "category_id": "cat-water-001", "department_id": "dept-sanit-002"},
        {"id": "map-002", "category_id": "cat-power-002", "department_id": "dept-maint-001"}
    ]
    mock_complaints = [
        {
            "id": "comp-uuid-001",
            "complaint_number": "VC-2026-0001",
            "patient_name": "Ramesh Kumar",
            "patient_phone": "+91-9876543210",
            "description": "Ward 3B light flickering",
            "language": "en",
            "category_id": "cat-power-002",
            "department_id": "dept-maint-001",
            "priority": "medium",
            "status": "received",
            "assigned_to": None,
            "resolved_at": None,
            "created_at": "2026-11-07T08:00:00Z",
            "updated_at": "2026-11-07T08:00:00Z"
        }
    ]

    mock_client._sample_departments = mock_departments
    mock_client._sample_categories = mock_categories
    mock_client._sample_mappings = mock_mappings
    mock_client._sample_complaints = mock_complaints

    return mock_client


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def auth_headers_admin():
    return {
        "X-User-Id": "admin-user-001",
        "X-User-Role": UserRole.HOSPITAL_ADMIN.value
    }


@pytest.fixture
def auth_headers_maintenance_staff():
    return {
        "X-User-Id": "staff-user-001",
        "X-User-Role": UserRole.DEPARTMENT_STAFF.value,
        "X-Department-Id": "dept-maint-001"
    }


@pytest.fixture
def auth_headers_department_head():
    return {
        "X-User-Id": "head-user-001",
        "X-User-Role": UserRole.DEPARTMENT_HEAD.value,
        "X-Department-Id": "dept-maint-001"
    }


@pytest.fixture
def auth_headers_sanitation_staff():
    return {
        "X-User-Id": "staff-user-002",
        "X-User-Role": UserRole.DEPARTMENT_STAFF.value,
        "X-Department-Id": "dept-sanit-002"
    }
