"""Sarvam STT and TTS adapters used by the real patient terminal."""

import base64
import binascii
import mimetypes

import httpx

from app.config import settings

STT_URL = "https://api.sarvam.ai/speech-to-text"
TTS_URL = "https://api.sarvam.ai/text-to-speech"


class SarvamError(RuntimeError):
    pass


def _api_key() -> str:
    if settings.SARVAM_API_KEY is None or not settings.SARVAM_API_KEY.get_secret_value().strip():
        raise SarvamError("Speech service is not configured")
    return settings.SARVAM_API_KEY.get_secret_value()


async def transcribe(audio: bytes, filename: str, language_code: str | None) -> dict:
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    try:
        async with httpx.AsyncClient(timeout=settings.OPENROUTER_TIMEOUT_SECONDS) as client:
            response = await client.post(
                STT_URL,
                headers={"api-subscription-key": _api_key()},
                data={"model": "saaras:v4", **({"language_code": language_code} if language_code and language_code != "unknown" else {})},
                files={"file": (filename, audio, mime)},
            )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload.get("transcript"), str) or not payload["transcript"].strip():
            raise SarvamError("Speech recognition returned no transcript")
        return payload
    except SarvamError:
        raise
    except httpx.TimeoutException:
        raise SarvamError("Speech recognition timed out") from None
    except httpx.HTTPStatusError as exc:
        raise SarvamError(f"Speech recognition failed (HTTP {exc.response.status_code})") from None
    except (httpx.HTTPError, ValueError, TypeError):
        raise SarvamError("Speech recognition is temporarily unavailable") from None


async def synthesize(text: str, language_code: str) -> bytes:
    try:
        async with httpx.AsyncClient(timeout=settings.OPENROUTER_TIMEOUT_SECONDS) as client:
            response = await client.post(
                TTS_URL,
                headers={"api-subscription-key": _api_key()},
                json={"text": text, "language_code": language_code, "model": "bulbul:v3", "speaker": "shubh", "output_audio_codec": "wav"},
            )
        response.raise_for_status()
        return base64.b64decode(response.json()["audios"][0], validate=True)
    except SarvamError:
        raise
    except httpx.TimeoutException:
        raise SarvamError("Speech generation timed out") from None
    except httpx.HTTPStatusError as exc:
        raise SarvamError(f"Speech generation failed (HTTP {exc.response.status_code})") from None
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, binascii.Error):
        raise SarvamError("Speech generation is temporarily unavailable") from None
