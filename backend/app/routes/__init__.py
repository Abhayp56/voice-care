"""API Routes package."""
from app.routes.complaints import router as complaints_router
from app.routes.departments import router as departments_router
from app.routes.dashboard import router as dashboard_router
from app.routes.evidence import router as evidence_router
from app.routes.public import router as public_router

__all__ = [
    "complaints_router",
    "departments_router",
    "dashboard_router",
    "evidence_router",
    "public_router",
]

