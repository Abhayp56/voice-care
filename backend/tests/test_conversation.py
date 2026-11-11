from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.agents.conversation_agent import ConversationAgent
from app.main import app
from app.models.conversation import (
    ConversationAgentResponse,
)
from app.services.conversation_service import ConversationService
from app.services.conversation_sessions import InMemoryConversationSessionManager


class QueueAgent:
    def __init__(self, responses):
        self.responses = list(responses)

    async def process_message(self, *args, **kwargs):
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def ready_response(*, language="en-IN", description="Bathroom is unclean"):
    return ConversationAgentResponse(
        language=language,
        reply="The bathroom in Ward 4 is unclean. Is this summary correct?",
        facts={
            "title": "Unclean bathroom",
            "description": description,
            "category": "Sanitation",
            "location": "Ward 4",
        },
        summary="The bathroom in Ward 4 is unclean.",
        ready_for_confirmation=True,
    )


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def install_service(agent, *, ttl=1800):
    from app.routes.conversation import get_conversation_service

    service = ConversationService(agent=agent, sessions=InMemoryConversationSessionManager(ttl_seconds=ttl))
    app.dependency_overrides[get_conversation_service] = lambda: service
    return service


def complaint_repositories():
    complaint_repo = MagicMock()
    complaint_repo.create_complaint.return_value = {
        "id": "complaint-uuid-1",
        "complaint_number": "VC-2026-0001",
    }
    dept_repo = MagicMock()
    dept_repo.get_all_categories.return_value = [{"id": "category-uuid-1", "name": "Sanitation"}]
    dept_repo.get_category_by_id.return_value = {
        "id": "category-uuid-1", "name": "Sanitation", "default_priority": "high"
    }
    dept_repo.get_department_for_category.return_value = "department-uuid-1"
    dept_repo.get_department_by_id.return_value = {"id": "department-uuid-1", "name": "Sanitation"}
    history_repo = MagicMock()
    return complaint_repo, dept_repo, history_repo


def test_start_conversation_in_english_and_kannada(client):
    install_service(QueueAgent([]))
    english = client.post("/api/conversation/start", json={"language": "en-IN"})
    kannada = client.post("/api/conversation/start", json={"language": "kn-IN"})
    assert english.status_code == 200
    assert english.json()["state"] == "STARTED"
    assert "Hello" in english.json()["reply"]
    assert kannada.status_code == 200
    assert "ನಮಸ್ಕಾರ" in kannada.json()["reply"]


def test_follow_up_and_patient_correction_update_facts(client):
    install_service(QueueAgent([
        ConversationAgentResponse(
            language="en-IN",
            reply="Which ward is this in?",
            facts={"title": "Unclean bathroom", "description": "The bathroom is unclean", "category": "Sanitation"},
            missing_information=["location"],
        ),
        ready_response(description="The bathroom in Ward 4 is very unclean"),
        ready_response(description="The bathroom in Ward 4 is very unclean; corrected by patient"),
    ]))
    session_id = client.post("/api/conversation/start", json={}).json()["session_id"]
    first = client.post("/api/conversation/message", json={
        "session_id": session_id, "message": "The bathroom is unclean",
    })
    second = client.post("/api/conversation/message", json={
        "session_id": session_id, "message": "Ward 4, and it is very unclean",
    })
    assert first.json()["missing_information"] == ["location"]
    assert second.json()["state"] == "AWAITING_CONFIRMATION"
    corrected = client.post("/api/conversation/confirm", json={
        "session_id": session_id, "confirmed": False, "correction": "It is very unclean",
    })
    assert corrected.status_code == 200
    assert corrected.json()["state"] == "AWAITING_CONFIRMATION"
    assert corrected.json()["summary"] is not None


def test_kannada_conversation_and_confirmation(client):
    install_service(QueueAgent([ready_response(language="kn-IN")]))
    session_id = client.post("/api/conversation/start", json={"language": "kn-IN"}).json()["session_id"]
    message = client.post("/api/conversation/message", json={
        "session_id": session_id, "message": "ಶೌಚಾಲಯ ಅಶುಚಿಯಾಗಿದೆ",
    })
    confirmed = client.post("/api/conversation/confirm", json={"session_id": session_id, "confirmed": True})
    assert message.json()["language"] == "kn-IN"
    assert confirmed.json()["state"] == "CONFIRMED"
    assert confirmed.json()["complaint"]["patient_confirmed"] is True


def test_submission_requires_confirmation_then_uses_canonical_intake_once(client):
    install_service(QueueAgent([ready_response()]))
    complaint_repo, dept_repo, history_repo = complaint_repositories()
    from app.dependencies import get_complaint_repository, get_department_repository, get_status_history_repository

    app.dependency_overrides[get_complaint_repository] = lambda: complaint_repo
    app.dependency_overrides[get_department_repository] = lambda: dept_repo
    app.dependency_overrides[get_status_history_repository] = lambda: history_repo
    session_id = client.post("/api/conversation/start", json={}).json()["session_id"]
    client.post("/api/conversation/message", json={"session_id": session_id, "message": "Bathroom is dirty"})

    before_confirmation = client.post(f"/api/conversation/sessions/{session_id}/submit")
    assert before_confirmation.status_code == 409
    complaint_repo.create_complaint.assert_not_called()

    client.post("/api/conversation/confirm", json={"session_id": session_id, "confirmed": True})
    submitted = client.post(f"/api/conversation/sessions/{session_id}/submit")
    duplicate = client.post(f"/api/conversation/sessions/{session_id}/submit")
    assert submitted.status_code == 201
    assert submitted.json()["complaint_id"] == "complaint-uuid-1"
    assert duplicate.status_code == 409
    complaint_repo.create_complaint.assert_called_once()
    create_args = complaint_repo.create_complaint.call_args.kwargs
    assert create_args["category_id"] == "category-uuid-1"
    assert create_args["department_id"] == "department-uuid-1"
    assert create_args["priority"] == "high"
    assert create_args["priority"] != "critical"
    history_repo.record_transition.assert_called_once()


def test_invalid_category_mapping_does_not_create_complaint(client):
    install_service(QueueAgent([ready_response()]))
    complaint_repo, dept_repo, history_repo = complaint_repositories()
    dept_repo.get_all_categories.return_value = [{"id": "other-category", "name": "Billing"}]
    from app.dependencies import get_complaint_repository, get_department_repository, get_status_history_repository

    app.dependency_overrides[get_complaint_repository] = lambda: complaint_repo
    app.dependency_overrides[get_department_repository] = lambda: dept_repo
    app.dependency_overrides[get_status_history_repository] = lambda: history_repo
    session_id = client.post("/api/conversation/start", json={}).json()["session_id"]
    client.post("/api/conversation/message", json={"session_id": session_id, "message": "Bathroom is dirty"})
    client.post("/api/conversation/confirm", json={"session_id": session_id, "confirmed": True})

    response = client.post(f"/api/conversation/sessions/{session_id}/submit")
    assert response.status_code == 422
    complaint_repo.create_complaint.assert_not_called()


def test_cancel_and_emergency_bypass_provider(client):
    install_service(ConversationAgent())
    session_id = client.post("/api/conversation/start", json={}).json()["session_id"]
    cancelled = client.post("/api/conversation/message", json={
        "session_id": session_id, "message": "Please cancel complaint",
    })
    assert cancelled.json()["state"] == "CANCELLED"

    emergency_session = client.post("/api/conversation/start", json={}).json()["session_id"]
    emergency = client.post("/api/conversation/message", json={
        "session_id": emergency_session, "message": "I have chest pain",
    })
    assert emergency.json()["state"] == "EMERGENCY_REDIRECTED"
    assert "emergency" in emergency.json()["reply"].lower()


def test_expired_session_is_rejected(client):
    install_service(QueueAgent([]), ttl=0)
    session_id = client.post("/api/conversation/start", json={}).json()["session_id"]
    response = client.get(f"/api/conversation/{session_id}")
    assert response.status_code == 410


def test_ai_provider_failure_is_safe_and_existing_auth_routes_remain_protected(client, monkeypatch):
    from app.ai import openrouter_client

    monkeypatch.setattr(openrouter_client.settings, "OPENROUTER_API_KEY", None)
    monkeypatch.setattr(openrouter_client.settings, "CONVERSATION_MODEL", None)
    install_service(ConversationAgent())
    session_id = client.post("/api/conversation/start", json={}).json()["session_id"]
    failed = client.post("/api/conversation/message", json={
        "session_id": session_id, "message": "The waiting room is too cold",
    })
    protected = client.get("/api/complaints")
    assert failed.status_code == 503
    assert "key" not in failed.text.lower()
    assert protected.status_code == 401
    assert any(route.path == "/api/complaints" for route in app.routes)
