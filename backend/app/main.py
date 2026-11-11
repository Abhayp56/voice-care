import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database.supabase_client import check_supabase_connection, SupabaseConfigurationError, SupabaseConnectionError
from app.routes.complaints import router as complaints_router
from app.routes.departments import router as departments_router
from app.routes.dashboard import router as dashboard_router
from app.routes.evidence import router as evidence_router
from app.routes.public import router as public_router
from app.routes.conversation import router as conversation_router
from app.routes.voice import router as voice_router
from app.routes.orchestrator import router as orchestrator_router
from app.routes.auth import router as auth_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("voicecare_backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    logger.info("Initializing 4BIT VoiceCare Database Backend...")
    # Verify Supabase connectivity on startup
    health = check_supabase_connection()
    if health.get("status") == "connected":
        logger.info(f"Supabase connection verified: {settings.SUPABASE_URL}")
    else:
        logger.warning(f"Supabase connection warning on startup: {health.get('error')}")
    yield
    logger.info("Shutting down 4BIT VoiceCare Backend...")


app = FastAPI(
    title="4BIT VoiceCare Database Backend API",
    description="""
    ## 4BIT VoiceCare Backend Integration
    
    AI-powered, multilingual voice-based public grievance and hospital service monitoring system.
    Connects existing Supabase PostgreSQL tables and Storage to the application's backend.
    
    ### Key Modules & Capabilities:
    * **Complaint Lifecycle Management**: Creation, auto-routing via `department_mapping`, tracking, status transitions.
    * **AI Agents Integration**: Clean, validated interfaces for Patient Conversation Agent, Central Orchestrator, and Evidence Verification Agent.
    * **Department Dashboards**: Isolated department views, operational stats, overdue alert tracking.
    * **Resolution Evidence Storage**: Private 5MB image upload with signed URLs.
    * **Public Transparency Portal**: Privacy-safe views (`public_complaints_view`, `public_department_statistics`) with strict zero-PII guarantee.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
@app.exception_handler(SupabaseConfigurationError)
async def supabase_config_exception_handler(request: Request, exc: SupabaseConfigurationError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Database configuration error: {str(exc)}"}
    )

@app.exception_handler(SupabaseConnectionError)
async def supabase_conn_exception_handler(request: Request, exc: SupabaseConnectionError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": f"Database connection failure: {str(exc)}"}
    )


# Health Check
@app.get("/health", tags=["System"])
def health_check():
    """System health check endpoint verifying Supabase database connectivity."""
    db_health = check_supabase_connection()
    return {
        "status": "healthy" if db_health.get("status") == "connected" else "degraded",
        "service": "4BIT VoiceCare Backend",
        "environment": settings.ENVIRONMENT,
        "database": db_health
    }


@app.get("/", tags=["System"])
def root():
    """Welcome endpoint with API documentation links."""
    return {
        "message": "Welcome to 4BIT VoiceCare Backend API",
        "documentation": "/docs",
        "version": "1.0.0"
    }


# Include Routers
app.include_router(complaints_router)
app.include_router(departments_router)
app.include_router(dashboard_router)
app.include_router(evidence_router)
app.include_router(public_router)
app.include_router(conversation_router)
app.include_router(voice_router)
app.include_router(orchestrator_router)
app.include_router(auth_router)

