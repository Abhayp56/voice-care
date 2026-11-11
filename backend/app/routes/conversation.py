"""Patient conversation endpoints; complaint APIs remain the persistence authority."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import (
    get_complaint_repository,
    get_department_repository,
    get_status_history_repository,
)
from app.models.conversation import (
    ConfirmConversationRequest,
    ConversationMessageRequest,
    ConversationResponse,
    ConversationSubmissionResponse,
    StartConversationRequest,
    StartConversationResponse,
)
from app.services.conversation_service import (
    CategoryMappingError,
    ComplaintSubmissionUnavailable,
    ConversationService,
)
from app.services.conversation_sessions import SessionExpired, SessionNotFound
from app.ai.openrouter_client import ConversationProviderError

router = APIRouter(prefix="/api/conversation", tags=["patient-conversation"])


def get_conversation_service(
    department_repo=Depends(get_department_repository),
) -> ConversationService:
    return ConversationService(department_repo=department_repo)


def _raise_http_error(exc: Exception) -> None:
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, SessionExpired):
        raise HTTPException(status_code=410, detail="Conversation session expired") from None
    if isinstance(exc, SessionNotFound):
        raise HTTPException(status_code=404, detail="Conversation session not found") from None
    if isinstance(exc, CategoryMappingError):
        raise HTTPException(status_code=422, detail=str(exc)) from None
    if isinstance(exc, (ConversationProviderError, ComplaintSubmissionUnavailable)):
        raise HTTPException(status_code=503, detail=str(exc)) from None
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=409, detail=str(exc)) from None
    raise HTTPException(status_code=500, detail="Conversation request could not be completed") from None


@router.post("/start", response_model=StartConversationResponse)
async def start_conversation(
    request: StartConversationRequest = StartConversationRequest(),
    service: ConversationService = Depends(get_conversation_service),
) -> StartConversationResponse:
    try:
        return await service.start(request.language)
    except Exception as exc:
        _raise_http_error(exc)


@router.post("/message", response_model=ConversationResponse)
async def send_message(
    request: ConversationMessageRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    try:
        return await service.send_message(request.session_id, request.message)
    except Exception as exc:
        _raise_http_error(exc)


@router.post("/confirm", response_model=ConversationResponse)
async def confirm_complaint(
    request: ConfirmConversationRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    try:
        return await service.confirm(request.session_id, request.confirmed, request.correction)
    except Exception as exc:
        _raise_http_error(exc)


@router.post(
    "/sessions/{session_id}/submit",
    response_model=ConversationSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_confirmed_complaint(
    session_id: str,
    service: ConversationService = Depends(get_conversation_service),
    complaint_repo=Depends(get_complaint_repository),
    dept_repo=Depends(get_department_repository),
    history_repo=Depends(get_status_history_repository),
) -> ConversationSubmissionResponse:
    try:
        return await service.submit_confirmed(
            session_id,
            complaint_repo=complaint_repo,
            dept_repo=dept_repo,
            history_repo=history_repo,
        )
    except Exception as exc:
        _raise_http_error(exc)


@router.get("/{session_id}", response_model=ConversationResponse)
async def get_conversation(
    session_id: str,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    try:
        return await service.get(session_id)
    except Exception as exc:
        _raise_http_error(exc)
