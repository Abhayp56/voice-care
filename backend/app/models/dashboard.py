from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class DepartmentCount(BaseModel):
    department_id: str
    department_name: str
    count: int


class CategoryCount(BaseModel):
    category_id: str
    category_name: str
    count: int


class PriorityCount(BaseModel):
    priority: str
    count: int


class StatusCount(BaseModel):
    status: str
    count: int


class DashboardStatsResponse(BaseModel):
    total_complaints: int
    pending_complaints: int          # received, assigned
    in_progress_complaints: int      # in_progress, needs_review
    resolved_complaints: int         # resolved, closed
    escalated_complaints: int        # escalated
    overdue_complaints: int          # complaints pending/in_progress created > 48h or past escalation deadline
    average_resolution_hours: Optional[float] = None
    complaints_by_department: List[DepartmentCount] = []
    complaints_by_category: List[CategoryCount] = []
    complaints_by_priority: List[PriorityCount] = []
    complaints_by_status: List[StatusCount] = []

    model_config = ConfigDict(from_attributes=True)


class PublicDepartmentStatsResponse(BaseModel):
    """
    Public department statistics. Aggregate counts only, no PII.
    Corresponds to public_department_statistics database view.
    """
    department_name: str
    total_complaints: int
    resolved_count: int
    open_count: int

    model_config = ConfigDict(from_attributes=True)

