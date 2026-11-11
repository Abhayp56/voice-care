from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.status_history_repository import StatusHistoryRepository
from app.repositories.user_repository import UserRepository
from app.services.storage_service import StorageService
from app.services.dashboard_service import DashboardService
from app.services.publication_service import PublicationService


def get_complaint_repository() -> ComplaintRepository:
    return ComplaintRepository()


def get_department_repository() -> DepartmentRepository:
    return DepartmentRepository()


def get_evidence_repository() -> EvidenceRepository:
    return EvidenceRepository()


def get_status_history_repository() -> StatusHistoryRepository:
    return StatusHistoryRepository()


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_storage_service() -> StorageService:
    return StorageService()


def get_dashboard_service() -> DashboardService:
    return DashboardService()


def get_publication_service() -> PublicationService:
    return PublicationService()

