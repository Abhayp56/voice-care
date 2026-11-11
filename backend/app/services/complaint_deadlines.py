"""Calendar-age escalation policy for unresolved complaints."""

from datetime import datetime, timezone
from typing import Any

COMPLETED_STATUSES = {"resolved", "closed"}
HIGHER_AUTHORITY_AFTER_DAYS = 11


def complaint_age_days(complaint: dict[str, Any], *, now: datetime | None = None) -> int:
    created_at = complaint.get("created_at")
    if not created_at:
        return 0
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            return 0
    if not isinstance(created_at, datetime):
        return 0
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    return max(0, (current - created_at.astimezone(timezone.utc)).days)


def is_higher_authority_case(complaint: dict[str, Any], *, now: datetime | None = None) -> bool:
    return (
        str(complaint.get("status", "")).lower() not in COMPLETED_STATUSES
        and complaint_age_days(complaint, now=now) >= HIGHER_AUTHORITY_AFTER_DAYS
    )


def escalation_metadata(complaint: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    age = complaint_age_days(complaint, now=now)
    active = str(complaint.get("status", "")).lower() not in COMPLETED_STATUSES
    stage = "none"
    warning_level = 0
    if active and age >= HIGHER_AUTHORITY_AFTER_DAYS:
        stage = "higher_authority"
    elif active and age >= 9:
        stage = "warning_2"
        warning_level = 2
    elif active and age >= 7:
        stage = "warning_1"
        warning_level = 1
    return {
        "days_open": age,
        "warning_level": warning_level,
        "escalation_stage": stage,
        "higher_authority_review": stage == "higher_authority",
    }
