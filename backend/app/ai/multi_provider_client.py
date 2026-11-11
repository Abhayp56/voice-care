"""Gemini/Groq adapter with role-specific models and safe provider fallback."""

import base64
import json
import logging
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.ai.openrouter_client import ConversationProviderError

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class AIProviderError(ConversationProviderError):
    """A safe, user-facing error that never includes provider response bodies."""


class MultiProviderClient:
    def __init__(self, role: str, *, timeout: float | None = None) -> None:
        if role not in {"conversation", "orchestrator", "verification"}:
            raise ValueError("Unknown AI role")
        self.role = role
        self.timeout = timeout or settings.OPENROUTER_TIMEOUT_SECONDS

    def _providers(self) -> list[tuple[str, str, str]]:
        order = getattr(settings, f"AI_{self.role.upper()}_PROVIDERS")
        providers: list[tuple[str, str, str]] = []
        for name in (item.strip().lower() for item in order.split(",")):
            if name == "gemini":
                key = getattr(settings, f"GEMINI_{self.role.upper()}_API_KEY")
                if key is None or not key.get_secret_value().strip():
                    key = settings.GEMINI_API_KEY
                model = getattr(settings, f"GEMINI_{self.role.upper()}_MODEL")
            elif name == "groq":
                key = getattr(settings, f"GROQ_{self.role.upper()}_API_KEY")
                if key is None or not key.get_secret_value().strip():
                    key = settings.GROQ_API_KEY
                model = getattr(settings, f"GROQ_{self.role.upper()}_MODEL")
            else:
                continue
            if key and key.get_secret_value().strip() and model and model.strip():
                providers.append((name, key.get_secret_value(), model.strip()))
        return providers

    async def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        response_model: type[T],
        images: list[tuple[bytes, str]] | None = None,
    ) -> T:
        providers = self._providers()
        if not providers:
            raise AIProviderError(f"No Gemini or Groq {self.role} provider is configured")

        for provider, key, model in providers:
            try:
                raw = await self._request(provider, key, model, messages, response_model, images or [])
                return response_model.model_validate_json(raw)
            except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, ValidationError) as exc:
                logger.warning("AI provider request failed; role=%s provider=%s error_type=%s", self.role, provider, type(exc).__name__)
        raise AIProviderError(f"All configured {self.role} AI providers are unavailable")

    async def _request(self, provider, key, model, messages, response_model, images) -> str:
        schema_prompt = (
            "Return exactly one JSON object matching this schema. Do not include markdown: "
            + json.dumps(response_model.model_json_schema(), ensure_ascii=False)
        )
        if provider == "gemini":
            system = "\n\n".join(
                [schema_prompt, *(m["content"] for m in messages if m.get("role") == "system" and isinstance(m.get("content"), str))]
            )
            contents = []
            for message in messages:
                role = message.get("role")
                if role == "system":
                    continue
                contents.append({"role": "model" if role == "assistant" else "user", "parts": [{"text": str(message.get("content", ""))}]})
            if not contents:
                contents = [{"role": "user", "parts": [{"text": "Respond with the requested JSON."}]}]
            if images:
                contents[-1]["parts"].extend({"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode("ascii")}} for data, mime in images)
            url = f"{settings.GEMINI_BASE_URL.rstrip('/')}/models/{model}:generateContent"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                    json={"systemInstruction": {"parts": [{"text": system}]}, "contents": contents, "generationConfig": {"responseMimeType": "application/json"}},
                )
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]

        request_messages = [{"role": "system", "content": schema_prompt}, *[dict(message) for message in messages]]
        if images:
            last = request_messages[-1]
            image_parts = [{"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"}} for data, mime in images]
            last["content"] = [{"type": "text", "text": str(last.get("content", ""))}, *image_parts]
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{settings.GROQ_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "messages": request_messages, "stream": False, "response_format": {"type": "json_object"}},
            )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise TypeError("Provider returned non-text content")
        return content
