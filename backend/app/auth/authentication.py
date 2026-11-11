import logging
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database.supabase_client import get_supabase_client
from app.repositories.user_repository import UserRepository
from app.dependencies import get_user_repository
from app.models.user import AuthenticatedUser, UserRole
from app.config import settings

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_department_id: Optional[str] = Header(None, alias="X-Department-Id"),
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthenticatedUser:
    """
    FastAPI dependency that extracts and verifies the authenticated user.
    
    Supabase bearer tokens are verified remotely and mapped to a trusted profile.
    Mock identity headers are accepted only when explicitly enabled in development.
    """
    # 1. Check Bearer token
    if credentials and credentials.credentials:
        token = credentials.credentials
        try:
            client = get_supabase_client()
            auth_response = client.auth.get_user(token)
            if not auth_response or not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired Supabase authentication token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user_data = auth_response.user
            user_id = str(user_data.id)
            email = user_data.email

            # Query profile from public.profiles table
            try:
                profile = user_repo.get_profile_by_id(user_id)
            except Exception as exc:
                logger.error("Could not load authenticated user profile")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Unable to load user authorization profile.",
                ) from exc

            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="A trusted staff profile is required.",
                )

            try:
                role = UserRole(profile["role"])
            except (KeyError, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="The staff profile has no valid role.",
                )
            dept_id = profile.get("department_id")
            full_name = profile.get("full_name")
            if role == UserRole.DEPARTMENT_STAFF:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="The frontline staff dashboard has been retired. Use a department head or hospital administrator account.",
                )

            return AuthenticatedUser(
                id=user_id,
                email=email,
                full_name=full_name,
                role=role,
                department_id=dept_id,
                department_name=profile.get("department_name"),
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("Supabase auth token verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Never accept caller-provided identity headers outside explicit local development mode.
    dev_headers_enabled = (
        settings.ENVIRONMENT.lower() == "development"
        and settings.ALLOW_DEV_AUTH_HEADERS
    )
    if dev_headers_enabled and x_user_id:
        try:
            role = UserRole(x_user_role) if x_user_role else UserRole.DEPARTMENT_STAFF
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid development role.")
        if role == UserRole.DEPARTMENT_STAFF:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The frontline staff dashboard has been retired.")

        return AuthenticatedUser(
            id=x_user_id,
            role=role,
            department_id=x_department_id,
            full_name="Test / Service User"
        )

    # Ignore X-User-* headers unless explicit local development mode is enabled.
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication credentials. Please provide Bearer token in Authorization header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Optional[AuthenticatedUser]:
    """Optional authentication dependency for endpoints that have public or anonymous modes."""
    if not credentials or not credentials.credentials:
        return None
    # An invalid supplied token is an authentication failure, never an anonymous fallback.
    return await get_current_user(credentials=credentials, user_repo=user_repo)
