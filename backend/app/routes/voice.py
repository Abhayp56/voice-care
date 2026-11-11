"""Validated speech endpoints for the patient terminal."""

from pathlib import PurePath
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.sarvam_voice import SarvamError, transcribe, synthesize

router = APIRouter(prefix="/api/voice", tags=["voice"])
MAX_AUDIO_BYTES = 10 * 1024 * 1024
ALLOWED_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".webm", ".mp4"}


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2500)
    language_code: str = Field(pattern=r"^(kn-IN|en-IN)$")


@router.post("/transcribe")
async def transcribe_audio(
    file: Annotated[UploadFile, File()],
    language_code: Annotated[str, Form(pattern=r"^(kn-IN|en-IN|unknown)$")] = "unknown",
) -> dict:
    filename = file.filename or "recording.webm"
    if PurePath(filename).suffix.lower() not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Unsupported audio format")
    audio = await file.read(MAX_AUDIO_BYTES + 1)
    if not audio:
        raise HTTPException(status_code=400, detail="Audio file is empty")
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio exceeds the 10 MB limit")
    try:
        return await transcribe(audio, filename, language_code)
    except SarvamError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


@router.post("/speak", responses={200: {"content": {"audio/wav": {}}}})
async def speak(request: SpeechRequest) -> Response:
    try:
        audio = await synthesize(request.text, request.language_code)
    except SarvamError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    return Response(content=audio, media_type="audio/wav")
