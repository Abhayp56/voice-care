"""Current authenticated staff profile."""
from fastapi import APIRouter, Depends

from app.auth.authentication import get_current_user
from app.models.user import AuthenticatedUser

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/me", response_model=AuthenticatedUser)
def get_my_profile(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    return user
