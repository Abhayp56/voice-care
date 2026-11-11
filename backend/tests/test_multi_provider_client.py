import httpx
import pytest
from pydantic import BaseModel, SecretStr

from app.ai.multi_provider_client import AIProviderError, MultiProviderClient
from app.config import settings


class Answer(BaseModel):
    answer: str


@pytest.mark.asyncio
async def test_gemini_failure_falls_back_to_groq_without_exposing_credentials(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", SecretStr("gemini-test-key"))
    monkeypatch.setattr(settings, "GROQ_API_KEY", SecretStr("groq-test-key"))
    monkeypatch.setattr(settings, "AI_CONVERSATION_PROVIDERS", "gemini,groq")
    monkeypatch.setattr(settings, "GEMINI_CONVERSATION_MODEL", "gemini-test-model")
    monkeypatch.setattr(settings, "GROQ_CONVERSATION_MODEL", "groq-test-model")
    requested = []

    class FakeClient:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs):
            requested.append(url)
            if "generativelanguage" in url:
                return httpx.Response(503, json={"error": {"message": "private test detail"}}, request=httpx.Request("POST", url))
            return httpx.Response(200, json={"choices": [{"message": {"content": '{"answer":"ok"}'}}]}, request=httpx.Request("POST", url))

    monkeypatch.setattr("app.ai.multi_provider_client.httpx.AsyncClient", FakeClient)
    result = await MultiProviderClient("conversation").complete(
        messages=[{"role": "user", "content": "hello"}], response_model=Answer
    )
    assert result.answer == "ok"
    assert len(requested) == 2
    assert "gemini-test-key" not in str(result)


@pytest.mark.asyncio
async def test_unconfigured_ai_fails_without_making_a_request(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(settings, "GROQ_API_KEY", None)
    monkeypatch.setattr(settings, "AI_CONVERSATION_PROVIDERS", "gemini,groq")
    monkeypatch.setattr(settings, "GEMINI_CONVERSATION_MODEL", None)
    monkeypatch.setattr(settings, "GROQ_CONVERSATION_MODEL", None)
    with pytest.raises(AIProviderError, match="No Gemini or Groq"):
        await MultiProviderClient("conversation").complete(
            messages=[{"role": "user", "content": "hello"}], response_model=Answer
        )


def test_voice_and_agent_routes_are_registered():
    from app.main import app

    paths = {route.path for route in app.routes}
    assert "/api/voice/transcribe" in paths
    assert "/api/voice/speak" in paths
    assert "/api/orchestrator/assess" in paths
    assert "/api/evidence/{evidence_id}/analyze" in paths
