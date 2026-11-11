from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    default_priority: str = Field(default="medium")


class ComplaintCategoryCreate(ComplaintCategoryBase):
    pass


class ComplaintCategoryResponse(ComplaintCategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentMappingResponse(BaseModel):
    id: str
    category_id: str
    department_id: str
    created_at: datetime
    category_name: Optional[str] = None
    department_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

