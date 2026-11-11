from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StatusHistoryCreate(BaseModel):
    complaint_id: str
    old_status: Optional[str] = None
    new_status: str
    changed_by: Optional[str] = None
    note: Optional[str] = None


class StatusHistoryResponse(BaseModel):
    id: str
    complaint_id: str
    old_status: Optional[str] = None
    new_status: str
    changed_by: Optional[str] = None
    changed_by_name: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

