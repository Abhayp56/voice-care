import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from supabase import Client
from app.database.supabase_client import get_supabase_client
from app.models.dashboard import (
    DashboardStatsResponse,
    DepartmentCount,
    CategoryCount,
    PriorityCount,
    StatusCount
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Service responsible for aggregating and computing real-time operational statistics."""

    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()

    def get_dashboard_statistics(self, department_id: Optional[str] = None) -> DashboardStatsResponse:
        """
        Computes real-time statistics from live database records:
        - Total, pending, in-progress, resolved, escalated, and overdue complaints.
        - Breakdowns by department, category, priority, and status.
        - Real average resolution time in hours.
        """
        try:
            # Query all relevant complaints
            query = self.client.table("complaints").select(
                "id, status, priority, department_id, category_id, created_at, resolved_at, "
                "departments(name), complaint_categories(name)"
            )
            if department_id:
                query = query.eq("department_id", department_id)

            response = query.execute()
            complaints = response.data or []

            total = len(complaints)
            pending = 0
            in_progress = 0
            resolved = 0
            escalated = 0
            overdue = 0

            dept_map: Dict[str, Dict[str, Any]] = {}
            cat_map: Dict[str, Dict[str, Any]] = {}
            priority_map: Dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            status_map: Dict[str, int] = {}
            resolution_durations_hours: List[float] = []

            now_utc = datetime.now(timezone.utc)

            for c in complaints:
                st = (c.get("status") or "received").lower()
                status_map[st] = status_map.get(st, 0) + 1

                # Grouping by status category
                if st in ["received", "assigned"]:
                    pending += 1
                elif st in ["in_progress", "needs_review"]:
                    in_progress += 1
                elif st in ["resolved", "closed"]:
                    resolved += 1
                elif st == "escalated":
                    escalated += 1

                # Priority counts
                pri = (c.get("priority") or "medium").lower()
                priority_map[pri] = priority_map.get(pri, 0) + 1

                # Department counts
                d_id = c.get("department_id")
                d_obj = c.get("departments") or {}
                d_name = d_obj.get("name") if isinstance(d_obj, dict) else "Unknown"
                if d_id:
                    if d_id not in dept_map:
                        dept_map[d_id] = {"id": d_id, "name": d_name, "count": 0}
                    dept_map[d_id]["count"] += 1

                # Category counts
                c_id = c.get("category_id")
                c_obj = c.get("complaint_categories") or {}
                c_name = c_obj.get("name") if isinstance(c_obj, dict) else "General"
                if c_id:
                    if c_id not in cat_map:
                        cat_map[c_id] = {"id": c_id, "name": c_name, "count": 0}
                    cat_map[c_id]["count"] += 1

                # Overdue detection (> 48 hours without resolution, or escalated)
                created_str = c.get("created_at")
                if created_str and st not in ["resolved", "closed"]:
                    try:
                        created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                        age_hours = (now_utc - created_dt).total_seconds() / 3600
                        if age_hours > 48 or st == "escalated":
                            overdue += 1
                    except Exception:
                        pass

                # Resolution duration calculation
                if st in ["resolved", "closed"] and c.get("resolved_at") and created_str:
                    try:
                        created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                        resolved_dt = datetime.fromisoformat(c["resolved_at"].replace("Z", "+00:00"))
                        duration = (resolved_dt - created_dt).total_seconds() / 3600
                        if duration >= 0:
                            resolution_durations_hours.append(duration)
                    except Exception:
                        pass

            avg_res_time = (
                round(sum(resolution_durations_hours) / len(resolution_durations_hours), 2)
                if resolution_durations_hours
                else None
            )

            return DashboardStatsResponse(
                total_complaints=total,
                pending_complaints=pending,
                in_progress_complaints=in_progress,
                resolved_complaints=resolved,
                escalated_complaints=escalated,
                overdue_complaints=overdue,
                average_resolution_hours=avg_res_time,
                complaints_by_department=[
                    DepartmentCount(department_id=v["id"], department_name=v["name"], count=v["count"])
                    for v in dept_map.values()
                ],
                complaints_by_category=[
                    CategoryCount(category_id=v["id"], category_name=v["name"], count=v["count"])
                    for v in cat_map.values()
                ],
                complaints_by_priority=[
                    PriorityCount(priority=k, count=v) for k, v in priority_map.items() if v > 0
                ],
                complaints_by_status=[
                    StatusCount(status=k, count=v) for k, v in status_map.items()
                ]
            )
        except Exception as e:
            logger.error(f"Error compiling dashboard statistics: {str(e)}")
            raise

