"""Small OpenRouter chat client with safe errors and Pydantic output validation."""

import json
import logging
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


class ConversationProviderError(RuntimeError):
    """Provider failures without provider response bodies or credential details."""


class OpenRouterClient:
    async def complete(self, *, messages: list[dict[str, str]], response_model: type[T]) -> T:
        key = settings.OPENROUTER_API_KEY
        model = settings.CONVERSATION_MODEL
        if key is None or not key.get_secret_value().strip() or not model or not model.strip():
            raise ConversationProviderError("Conversation AI is not configured")

        request_messages = [dict(message) for message in messages]
        request_messages.insert(0, {
            "role": "system",
            "content": "Return exactly one JSON object matching this schema: "
            + json.dumps(response_model.model_json_schema(), ensure_ascii=False),
        })
        try:
            async with httpx.AsyncClient(timeout=settings.OPENROUTER_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    OPENROUTER_CHAT_URL,
                    headers={"Authorization": f"Bearer {key.get_secret_value()}", "Content-Type": "application/json"},
                    json={"model": model, "messages": request_messages, "stream": False},
                )
            response.raise_for_status()
        except httpx.TimeoutException:
            logger.warning("OpenRouter conversation request timed out")
            raise ConversationProviderError("Conversation AI took too long to respond") from None
        except httpx.HTTPStatusError as exc:
            logger.warning("OpenRouter conversation request failed; status=%d", exc.response.status_code)
            raise ConversationProviderError("Conversation AI is temporarily unavailable") from None
        except httpx.HTTPError:
            logger.warning("OpenRouter conversation transport failed")
            raise ConversationProviderError("Conversation AI could not be reached") from None

        try:
            content = response.json()["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError
            return response_model.model_validate_json(content)
        except (ValueError, KeyError, IndexError, TypeError, ValidationError):
            logger.warning("OpenRouter returned an invalid conversation response")
            raise ConversationProviderError("Conversation AI returned an unreadable response") from None
