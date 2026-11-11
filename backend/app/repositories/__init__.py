"""Repository modules for 4BIT VoiceCare database operations."""
from app.repositories.department_repository import DepartmentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.status_history_repository import StatusHistoryRepository

__all__ = [
    "DepartmentRepository",
    "UserRepository",
    "ComplaintRepository",
    "EvidenceRepository",
    "StatusHistoryRepository",
]

