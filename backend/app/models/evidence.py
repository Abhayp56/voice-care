from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class EvidenceCreate(BaseModel):
    complaint_id: str = Field(..., description="UUID of associated complaint")
    file_path: str = Field(..., description="Path of uploaded file in Supabase Storage")
    file_type: str = Field("image", description="File type: image, note, document")
    notes: Optional[str] = Field(None, description="Resolution notes accompanying the evidence")
    submitted_by: Optional[str] = Field(None, description="UUID of staff profile submitting evidence")


class EvidenceVerificationRequest(BaseModel):
    verified: bool = Field(..., description="Whether evidence is verified as genuine resolution")
    notes: Optional[str] = Field(None, description="Verification remarks")


class EvidenceResponse(BaseModel):
    id: str
    complaint_id: str
    file_path: str
    file_type: str
    notes: Optional[str] = None
    submitted_by: Optional[str] = None
    submitted_by_name: Optional[str] = None
    verified_by: Optional[str] = None
    verified_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_accuracy_m: Optional[float] = None
    created_at: datetime
    signed_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

