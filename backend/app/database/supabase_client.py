import logging
from typing import Optional
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)

class SupabaseConfigurationError(Exception):
    """Raised when Supabase credentials or environment variables are missing/invalid."""
    pass

class SupabaseConnectionError(Exception):
    """Raised when unable to establish connection with Supabase."""
    pass

_supabase_admin_client: Optional[Client] = None
_supabase_anon_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get the singleton Supabase client authenticated with the service role key.
    Used for trusted backend operations, bypassing client-side RLS restrictions securely.
    Never expose this client or its key to the frontend or AI clients.
    """
    global _supabase_admin_client
    if _supabase_admin_client is not None:
        return _supabase_admin_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        error_msg = "SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is not configured."
        logger.error(error_msg)
        raise SupabaseConfigurationError(error_msg)

    try:
        _supabase_admin_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY.get_secret_value()
        )
        logger.info("Supabase service-role client initialized successfully.")
        return _supabase_admin_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        raise SupabaseConnectionError(f"Could not connect to Supabase: {str(e)}") from e


def get_supabase_anon_client() -> Client:
    """
    Get the singleton Supabase client authenticated with the anonymous key.
    Enforces Row Level Security (RLS) as configured in Supabase.
    """
    global _supabase_anon_client
    if _supabase_anon_client is not None:
        return _supabase_anon_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        error_msg = "SUPABASE_URL or SUPABASE_ANON_KEY is not configured."
        logger.error(error_msg)
        raise SupabaseConfigurationError(error_msg)

    try:
        _supabase_anon_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY.get_secret_value()
        )
        logger.info("Supabase anon client initialized successfully.")
        return _supabase_anon_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase anon client: {str(e)}")
        raise SupabaseConnectionError(f"Could not connect to Supabase: {str(e)}") from e


def check_supabase_connection() -> dict:
    """
    Health check helper to verify Supabase connectivity and access to core tables.
    Returns status dict with response time and table check results.
    """
    try:
        client = get_supabase_client()
        # Probe departments table as a lightweight connectivity check
        response = client.table("departments").select("id", count="exact").limit(1).execute()
        return {
            "status": "connected",
            "database": "reachable",
            "url": settings.SUPABASE_URL,
            "department_records_detected": response.count if hasattr(response, "count") else len(response.data)
        }
    except Exception as e:
        logger.error(f"Supabase health check failed: {str(e)}")
        return {
            "status": "error",
            "database": "unreachable",
            "error": str(e)
        }
