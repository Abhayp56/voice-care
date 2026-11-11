from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UserRole(str, Enum):
    DEPARTMENT_STAFF = "department_staff"
    DEPARTMENT_HEAD = "department_head"
    HOSPITAL_ADMIN = "hospital_admin"
    HIGHER_AUTHORITY = "higher_authority"


class UserProfileBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = Field(default=UserRole.DEPARTMENT_STAFF)
    department_id: Optional[str] = None


class UserProfileCreate(UserProfileBase):
    id: str = Field(..., description="Corresponds to Supabase auth.users.id")


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    department_id: Optional[str] = None


class UserProfileResponse(UserProfileBase):
    id: str
    department_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthenticatedUser(BaseModel):
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.DEPARTMENT_STAFF
    department_id: Optional[str] = None
    department_name: Optional[str] = None

