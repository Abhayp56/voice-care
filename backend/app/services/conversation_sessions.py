"""Process-local prototype session store. Sessions do not survive restarts."""

import asyncio
import time
from dataclasses import dataclass, field
from uuid import uuid4

from app.models.conversation import (
    ComplaintFacts,
    ComplaintField,
    ConversationLanguage,
    ConversationState,
)

SESSION_TTL_SECONDS = 30 * 60


class SessionNotFound(LookupError):
    pass


class SessionExpired(LookupError):
    pass


@dataclass
class ConversationSession:
    session_id: str
    language: ConversationLanguage
    state: ConversationState = ConversationState.STARTED
    facts: ComplaintFacts = field(default_factory=ComplaintFacts)
    missing_information: list[ComplaintField] = field(default_factory=list)
    summary: str | None = None
    history: list[dict[str, str]] = field(default_factory=list)
    asked_questions: list[str] = field(default_factory=list)
    correction_pending: bool = False
    last_reply: str = ""
    complaint_id: str | None = None
    complaint_number: str | None = None
    created_at: float = field(default_factory=time.monotonic)
    last_activity: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


class InMemoryConversationSessionManager:
    """Temporary session store; use a durable adapter for multi-worker deployments."""

    def __init__(self, *, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, ConversationSession] = {}
        self._expired: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def create(self, language: ConversationLanguage) -> ConversationSession:
        async with self._lock:
            now = time.monotonic()
            for expired_id, old_session in list(self._sessions.items()):
                if now - old_session.last_activity >= self.ttl_seconds:
                    self._sessions.pop(expired_id, None)
                    self._expired[expired_id] = now
            self._prune_expired_tombstones()
            session = ConversationSession(session_id=str(uuid4()), language=language)
            self._sessions[session.session_id] = session
            return session

    async def get(self, session_id: str) -> ConversationSession:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                if session_id in self._expired:
                    raise SessionExpired(session_id)
                raise SessionNotFound(session_id)
            now = time.monotonic()
            if now - session.last_activity >= self.ttl_seconds:
                self._sessions.pop(session_id, None)
                self._expired[session_id] = now
                raise SessionExpired(session_id)
            session.last_activity = now
            return session

    async def touch(self, session: ConversationSession) -> None:
        async with self._lock:
            if self._sessions.get(session.session_id) is not session:
                raise SessionNotFound(session.session_id)
            session.last_activity = time.monotonic()

    def _prune_expired_tombstones(self) -> None:
        cutoff = time.monotonic() - self.ttl_seconds
        self._expired = {key: value for key, value in self._expired.items() if value >= cutoff}


session_manager = InMemoryConversationSessionManager()
