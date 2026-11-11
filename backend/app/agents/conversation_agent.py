"""Patient conversation agent: drafts structured facts but cannot create complaints."""

import json
from pathlib import Path

from app.ai.multi_provider_client import MultiProviderClient
from app.models.conversation import (
    ComplaintFacts,
    ConversationAgentResponse,
    ConversationLanguage,
)

_PROMPT = Path(__file__).parents[1].joinpath("ai", "prompts", "conversation.md").read_text(encoding="utf-8")
_EMERGENCY_TERMS = (
    "emergency", "heart attack", "chest pain", "difficulty breathing", "can't breathe",
    "cannot breathe", "severe bleeding", "unconscious", "stroke", "suicidal",
    "ತೀವ್ರ ಎದೆ ನೋವು", "ಉಸಿರಾಡಲು ಆಗುತ್ತಿಲ್ಲ", "ಉಸಿರಾಟ ತೊಂದರೆ", "ಪ್ರಜ್ಞೆ ತಪ್ಪಿ", "ತೀವ್ರ ರಕ್ತಸ್ರಾವ", "ಹೃದಯಾಘಾತ",
)
_CANCEL_TERMS = ("cancel complaint", "stop complaint", "don't want to complain", "ದೂರು ರದ್ದು", "ರದ್ದು")
_LANGUAGE_REQUESTS = {
    ConversationLanguage.ENGLISH: ("speak english", "in english", "ಇಂಗ್ಲಿಷ್ ನಲ್ಲಿ", "ಇಂಗ್ಲಿಷಿನಲ್ಲಿ"),
    ConversationLanguage.KANNADA: ("speak kannada", "in kannada", "ಕನ್ನಡದಲ್ಲಿ", "ಕನ್ನಡ ಮಾತಾಡಿ"),
}


def requested_language(text: str, current: ConversationLanguage) -> ConversationLanguage:
    folded = text.casefold()
    for language, phrases in _LANGUAGE_REQUESTS.items():
        if any(phrase in folded for phrase in phrases):
            return language
    return current


class ConversationAgent:
    def __init__(self, client: MultiProviderClient | None = None) -> None:
        self.client = client or MultiProviderClient("conversation")

    async def process_message(
        self,
        patient_text: str,
        *,
        language: ConversationLanguage,
        facts: ComplaintFacts | None = None,
        history: list[dict[str, str]] | None = None,
        asked_questions: list[str] | None = None,
        correction_pending: bool = False,
        available_categories: list[str] | None = None,
        hospital_context: dict | None = None,
    ) -> ConversationAgentResponse:
        folded = patient_text.casefold()
        language = requested_language(patient_text, language)
        if any(term in folded for term in _EMERGENCY_TERMS):
            reply = (
                "Please contact the hospital emergency desk immediately. I cannot assess medical emergencies here."
                if language == ConversationLanguage.ENGLISH
                else "ದಯವಿಟ್ಟು ಕೂಡಲೇ ಆಸ್ಪತ್ರೆಯ ತುರ್ತು ಚಿಕಿತ್ಸಾ ವಿಭಾಗವನ್ನು ಸಂಪರ್ಕಿಸಿ. ಇಲ್ಲಿ ತುರ್ತು ವೈದ್ಯಕೀಯ ಪರಿಸ್ಥಿತಿಯನ್ನು ಪರಿಶೀಲಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ."
            )
            return ConversationAgentResponse(language=language, reply=reply, emergency_redirect=True)
        if any(term in folded for term in _CANCEL_TERMS):
            reply = (
                "I have stopped this complaint conversation. Contact me again if you want to continue."
                if language == ConversationLanguage.ENGLISH
                else "ಈ ದೂರು ಸಂಭಾಷಣೆಯನ್ನು ನಿಲ್ಲಿಸಿದ್ದೇನೆ. ಮುಂದುವರಿಸಲು ಬಯಸಿದರೆ ಮತ್ತೆ ತಿಳಿಸಿ."
            )
            return ConversationAgentResponse(language=language, reply=reply, cancelled=True)

        context = {
            "preferred_language": language.value,
            "known_complaint_facts": (facts or ComplaintFacts()).model_dump(mode="json"),
            "questions_already_asked": (asked_questions or [])[-10:],
            "patient_rejected_previous_summary": correction_pending,
            "approved_hospital_categories": available_categories or [],
            "hospital_operational_context": hospital_context or {},
        }
        safe_history = [
            {"role": turn["role"], "content": turn["content"][:3000]}
            for turn in (history or [])[-16:]
            if turn.get("role") in {"user", "assistant"} and isinstance(turn.get("content"), str)
        ]
        result = await self.client.complete(
            messages=[
                {"role": "system", "content": _PROMPT},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
                *safe_history,
                {"role": "user", "content": patient_text[:4000]},
            ],
            response_model=ConversationAgentResponse,
        )
        result.language = language
        return result
