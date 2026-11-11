"""Conversation state machine and confirmed-patient handoff to canonical intake."""

import logging
import re
import unicodedata
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from app.agents.conversation_agent import ConversationAgent
from app.agents.orchestrator_agent import OrchestratorAgent
from app.ai.hospital_context import build_hospital_context
from app.ai.multi_provider_client import AIProviderError
from app.models.complaint import ComplaintCreate
from app.models.conversation import (
    ComplaintFacts,
    ComplaintField,
    ConfirmedComplaint,
    ConversationAgentResponse,
    ConversationLanguage,
    ConversationState,
)
from app.services.complaint_intake import create_complaint_record
from app.services.conversation_sessions import (
    ConversationSession,
    InMemoryConversationSessionManager,
    SessionExpired,
    SessionNotFound,
    session_manager,
)

logger = logging.getLogger(__name__)
_AFFIRMATIVE = {
    "yes", "yeah", "yes thats right", "yes thats correct", "yes it is", "yes it is correct",
    "thats right", "thats correct", "correct", "i confirm", "yes i confirm",
    "ಹೌದು", "ಹೌದು ಸರಿ", "ಹೌದು ಸರಿಯಾಗಿದೆ", "ಸರಿ", "ಹೌದು ದೂರು ದಾಖಲಿಸಿ",
    "ಹೌದು ದಾಖಲಿಸಿ", "ಹೌದು ಮಾಡಿ", "ಹೌದು ಮುಂದುವರಿಸಿ", "ಅದೇ ಸಮಸ್ಯೆ", "ಸಮಸ್ಯೆ ಅದೇ",
}
_NEGATIVE = {"no", "no thats wrong", "incorrect", "not correct", "ಇಲ್ಲ", "ಸರಿಯಿಲ್ಲ", "ತಪ್ಪಾಗಿದೆ"}
_REQUIRED_FACTS = (
    ("description", ComplaintField.DESCRIPTION),
)


class CategoryMappingError(ValueError):
    pass


class ComplaintSubmissionUnavailable(RuntimeError):
    pass


def _explicit_confirmation(message: str) -> bool | None:
    normalized = "".join(
        "" if char in {"'", "’"} else (" " if unicodedata.category(char).startswith("P") else char)
        for char in message.casefold()
    )
    normalized = " ".join(normalized.split())
    if normalized in _NEGATIVE or normalized.startswith(("no thats wrong", "no thats not right")):
        return False
    if normalized in _AFFIRMATIVE or normalized.startswith(("yes thats right", "yes thats correct", "yes it is")):
        return True
    return None


def _merge_facts(existing: ComplaintFacts, extracted: ComplaintFacts) -> ComplaintFacts:
    merged = existing.model_dump()
    for field_name in extracted.model_fields_set:
        value = getattr(extracted, field_name)
        if value is not None:
            merged[field_name] = value
    return ComplaintFacts.model_validate(merged)


def _required_missing(facts: ComplaintFacts) -> list[ComplaintField]:
    return [field for name, field in _REQUIRED_FACTS if not getattr(facts, name)]


def _contains_kannada(text: str | None) -> bool:
    return bool(text and re.search(r"[\u0C80-\u0CFF]", text))


def _confirmed_data(session: ConversationSession) -> ConfirmedComplaint:
    if _required_missing(session.facts):
        raise ValueError("Required complaint details are missing")
    return ConfirmedComplaint(
        title=session.facts.title or "Hospital service issue",
        description=session.facts.description or "",
        category=session.facts.category,
        location=session.facts.location or "",
        specific_location=session.facts.specific_location,
        language=session.language,
        priority_suggestion=session.facts.priority_suggestion,
        missing_information=[],
        patient_confirmed=True,
    )


def _response(session: ConversationSession, reply: str | None = None):
    complaint = None
    if session.state in {ConversationState.CONFIRMED, ConversationState.SUBMITTED}:
        complaint = _confirmed_data(session)
    return {
        "session_id": session.session_id,
        "state": session.state,
        "language": session.language,
        "reply": reply if reply is not None else session.last_reply,
        "summary": session.summary,
        "draft": session.facts,
        "missing_information": session.missing_information,
        "complaint": complaint,
    }


class ConversationService:
    def __init__(
        self,
        *,
        agent: ConversationAgent | None = None,
        sessions: InMemoryConversationSessionManager | None = None,
        department_repo=None,
    ) -> None:
        self.agent = agent or ConversationAgent()
        self.sessions = sessions or session_manager
        self.department_repo = department_repo

    async def start(self, language: ConversationLanguage):
        session = await self.sessions.create(language)
        greeting = (
            "Hello. I can help report a hospital service problem. What happened?"
            if language == ConversationLanguage.ENGLISH
            else "ನಮಸ್ಕಾರ. ಆಸ್ಪತ್ರೆಯ ಸೇವಾ ಸಮಸ್ಯೆಯನ್ನು ದಾಖಲಿಸಲು ಸಹಾಯ ಮಾಡುತ್ತೇನೆ. ಏನು ಸಮಸ್ಯೆಯಾಗಿದೆ?"
        )
        session.last_reply = greeting
        session.history.append({"role": "assistant", "content": greeting})
        return {
            "session_id": session.session_id,
            "state": session.state,
            "language": session.language,
            "reply": greeting,
            "expires_in_seconds": self.sessions.ttl_seconds,
        }

    async def send_message(self, session_id: str, message: str):
        session = await self._load(session_id)
        async with session.lock:
            self._assert_active(session)
            decision = _explicit_confirmation(message)
            if session.state == ConversationState.AWAITING_CONFIRMATION and decision is True:
                if not session.summary or _required_missing(session.facts):
                    raise ValueError("A complete complaint summary is not ready for confirmation")
                session.state = ConversationState.CONFIRMED
                session.last_reply = "Confirmed."
                self._record_turn(session, message, session.last_reply)
            elif session.state == ConversationState.AWAITING_CONFIRMATION and decision is False:
                session.state = ConversationState.COLLECTING_INFORMATION
                session.summary = None
                session.correction_pending = True
                session.last_reply = self._localized(
                    session.language,
                    "What should I correct in the summary?",
                    "ಸಾರಾಂಶದಲ್ಲಿ ಏನು ತಿದ್ದುಪಡಿ ಮಾಡಬೇಕು?",
                )
                self._record_turn(session, message, session.last_reply)
            else:
                if session.state == ConversationState.STARTED:
                    session.state = ConversationState.COLLECTING_INFORMATION
                await self._process_message(session, message)
            await self.sessions.touch(session)
            return _response(session)

    async def confirm(self, session_id: str, confirmed: bool, correction: str | None = None):
        session = await self._load(session_id)
        async with session.lock:
            self._assert_active(session)
            if session.state != ConversationState.AWAITING_CONFIRMATION or not session.summary:
                raise ValueError("There is no complete complaint summary awaiting confirmation")
            if confirmed:
                if _required_missing(session.facts):
                    raise ValueError("Required complaint details are missing")
                session.state = ConversationState.CONFIRMED
                session.last_reply = "Confirmed."
                self._record_turn(session, "Patient confirmed the summary.", session.last_reply)
            else:
                session.state = ConversationState.COLLECTING_INFORMATION
                session.summary = None
                session.correction_pending = True
                if correction and correction.strip():
                    await self._process_message(session, correction.strip())
                else:
                    session.last_reply = self._localized(
                        session.language,
                        "What should I correct in the summary?",
                        "ಸಾರಾಂಶದಲ್ಲಿ ಏನು ತಿದ್ದುಪಡಿ ಮಾಡಬೇಕು?",
                    )
                    self._record_turn(session, "Patient rejected the summary.", session.last_reply)
            await self.sessions.touch(session)
            return _response(session)

    async def get(self, session_id: str):
        session = await self._load(session_id)
        async with session.lock:
            return _response(session)

    async def submit_confirmed(self, session_id: str, *, complaint_repo, dept_repo, history_repo):
        session = await self._load(session_id)
        async with session.lock:
            if session.state == ConversationState.SUBMITTED:
                raise ValueError("This conversation has already been submitted")
            if session.state != ConversationState.CONFIRMED:
                raise ValueError("Patient confirmation is required before complaint submission")
            confirmed = _confirmed_data(session)
            try:
                categories = await run_in_threadpool(dept_repo.get_all_categories)
                routing_assessment = None
                hospital_context = None
                mappings = []
                departments = []
                try:
                    mappings, departments = await run_in_threadpool(
                        lambda: (dept_repo.get_all_mappings(), dept_repo.get_all_departments())
                    )
                    hospital_context = build_hospital_context(categories, mappings, departments)
                    routing_assessment = await OrchestratorAgent().assess(
                        confirmed.model_dump(mode="json"),
                        departments,
                        hospital_context=hospital_context,
                    )
                except AIProviderError:
                    logger.warning("Orchestrator providers unavailable; using the database category mapping")
                except Exception:
                    logger.warning("Orchestrator context unavailable; using the database category mapping")
                category_id = None
                if routing_assessment and routing_assessment.suggested_category_id:
                    selected_route = next((
                        route for route in (hospital_context or {}).get("service_routes", [])
                        if str(route.get("approved_category_id")) == routing_assessment.suggested_category_id
                        and route.get("mapped_department_id")
                    ), None)
                    if selected_route:
                        category_id = routing_assessment.suggested_category_id
                if category_id is None and confirmed.category:
                    category_name = confirmed.category.strip().casefold()
                    fallback = [
                        item for item in categories
                        if isinstance(item.get("name"), str)
                        and item["name"].strip().casefold() == category_name
                    ]
                    if len(fallback) == 1 and fallback[0].get("id"):
                        category_id = str(fallback[0]["id"])
                if category_id is None:
                    raise CategoryMappingError(
                        "The complaint could not be matched to a configured hospital category. Please describe the issue more clearly and try again."
                    )
                selected_category = next(item for item in categories if str(item.get("id")) == category_id)
                title = routing_assessment.normalized_title if routing_assessment else confirmed.title
                summary = routing_assessment.normalized_summary if routing_assessment else confirmed.description
                location = (routing_assessment.normalized_location or confirmed.location) if routing_assessment else confirmed.location
                specific_location = (routing_assessment.normalized_specific_location or confirmed.specific_location) if routing_assessment else confirmed.specific_location
                english_fields = [title, summary, location, specific_location]
                if routing_assessment:
                    english_fields.append(routing_assessment.rationale)
                if any(_contains_kannada(value) for value in english_fields):
                    raise ComplaintSubmissionUnavailable(
                        "We understood your Kannada report, but could not prepare the English complaint record. Please try submitting once more."
                    )
                description_parts = [title, summary]
                location_parts = [part for part in (location, specific_location) if part]
                if location_parts:
                    description_parts.append(f"Reported location: {' — '.join(location_parts)}")
                if routing_assessment and routing_assessment.rationale:
                    description_parts.append(
                        f"AI operational handling suggestion (advisory; staff review required): {routing_assessment.rationale}"
                    )
                payload = ComplaintCreate(
                    description="\n\n".join(description_parts),
                    category_id=category_id,
                    language="kn" if confirmed.language == ConversationLanguage.KANNADA else "en",
                )
                created = await run_in_threadpool(
                    lambda: create_complaint_record(
                        payload,
                        complaint_repo=complaint_repo,
                        dept_repo=dept_repo,
                        history_repo=history_repo,
                    )
                )
            except (CategoryMappingError, ComplaintSubmissionUnavailable, HTTPException):
                raise
            except Exception:
                logger.warning("Conversation complaint submission failed")
                raise ComplaintSubmissionUnavailable("The complaint could not be submitted. Please try again.") from None

            session.state = ConversationState.SUBMITTED
            session.complaint_id = str(created.get("id", ""))
            session.complaint_number = str(created.get("complaint_number", ""))
            session.last_reply = self._localized(
                session.language,
                "Your complaint was submitted successfully.",
                "ನಿಮ್ಮ ದೂರನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಸಲ್ಲಿಸಲಾಗಿದೆ.",
            )
            await self.sessions.touch(session)
            return {
                "session_id": session.session_id,
                "state": ConversationState.SUBMITTED,
                "complaint_id": session.complaint_id,
                "complaint_number": session.complaint_number,
                "routed_category": selected_category.get("name") or "",
                "routed_department": created.get("department_name") or "",
                "routing_assessment": routing_assessment,
            }

    async def _process_message(self, session: ConversationSession, message: str) -> None:
        category_names: list[str] = []
        hospital_context: dict = {}
        if self.department_repo is not None:
            try:
                records, mappings, departments = await run_in_threadpool(
                    lambda: (
                        self.department_repo.get_all_categories(),
                        self.department_repo.get_all_mappings(),
                        self.department_repo.get_all_departments(),
                    )
                )
                category_names = [item["name"] for item in records if isinstance(item.get("name"), str) and item["name"].strip()]
                hospital_context = build_hospital_context(records, mappings, departments)
            except Exception:
                logger.warning("Approved hospital routing context could not be loaded")
        result: ConversationAgentResponse = await self.agent.process_message(
            message,
            language=session.language,
            facts=session.facts,
            history=session.history,
            asked_questions=session.asked_questions,
            correction_pending=session.correction_pending,
            available_categories=category_names,
            hospital_context=hospital_context,
        )
        session.language = result.language
        if result.emergency_redirect:
            session.state = ConversationState.EMERGENCY_REDIRECTED
            session.summary = None
        elif result.cancelled:
            session.state = ConversationState.CANCELLED
            session.summary = None
        else:
            session.facts = _merge_facts(session.facts, result.facts)
            if category_names and session.facts.category and session.facts.category.casefold() not in {name.casefold() for name in category_names}:
                session.facts.category = None
            required_missing = _required_missing(session.facts)
            reported_missing = [
                item for item in result.missing_information
                if item == ComplaintField.DESCRIPTION
            ]
            session.missing_information = list(dict.fromkeys([*required_missing, *reported_missing]))
            ready = result.ready_for_confirmation and not required_missing
            session.summary = result.summary if ready else None
            session.correction_pending = False
            session.state = (
                ConversationState.AWAITING_CONFIRMATION
                if ready
                else ConversationState.COLLECTING_INFORMATION
            )
        if session.state == ConversationState.AWAITING_CONFIRMATION and session.summary:
            session.last_reply = self._localized(
                session.language,
                f"I understood: {session.summary}. Is that the issue? Say yes to submit, or no and tell me what to correct.",
                f"ನಾನು ಹೀಗೆ ಅರ್ಥಮಾಡಿಕೊಂಡಿದ್ದೇನೆ: {session.summary}. ಇದೇ ಸಮಸ್ಯೆಯೇ? ಸಲ್ಲಿಸಲು ಹೌದು ಎಂದು ಹೇಳಿ, ಅಥವಾ ತಿದ್ದುಪಡಿ ಹೇಳಲು ಇಲ್ಲ ಎಂದು ಹೇಳಿ.",
            )
        else:
            session.last_reply = result.reply
        self._record_turn(session, message, session.last_reply)
        if "?" in session.last_reply:
            session.asked_questions.append(session.last_reply)
            session.asked_questions = session.asked_questions[-10:]

    @staticmethod
    def _record_turn(session: ConversationSession, user_text: str, reply: str) -> None:
        session.history.extend([
            {"role": "user", "content": user_text[:4000]},
            {"role": "assistant", "content": reply[:2500]},
        ])
        session.history = session.history[-40:]

    @staticmethod
    def _localized(language: ConversationLanguage, english: str, kannada: str) -> str:
        return english if language == ConversationLanguage.ENGLISH else kannada

    @staticmethod
    def _assert_active(session: ConversationSession) -> None:
        if session.state in {
            ConversationState.CONFIRMED,
            ConversationState.SUBMITTED,
            ConversationState.CANCELLED,
            ConversationState.EMERGENCY_REDIRECTED,
        }:
            raise ValueError(f"Conversation is {session.state.value.lower()}")

    async def _load(self, session_id: str) -> ConversationSession:
        return await self.sessions.get(session_id)
