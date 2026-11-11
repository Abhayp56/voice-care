import logging
from typing import List, Optional, Dict, Any
from supabase import Client
from app.database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class StatusHistoryRepository:
    """Repository handling status history tracking and audit trail for complaints."""

    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()

    def record_transition(
        self,
        complaint_id: str,
        new_status: str,
        old_status: Optional[str] = None,
        changed_by: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Insert a transition record into status_history."""
        try:
            payload = {
                "complaint_id": complaint_id,
                "old_status": old_status,
                "new_status": new_status,
                "changed_by": changed_by,
                "note": note
            }
            response = self.client.table("status_history").insert(payload).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error logging status transition for complaint {complaint_id}: {str(e)}")
            raise

    def get_history_by_complaint(self, complaint_id: str) -> List[Dict[str, Any]]:
        """Retrieve complete transition history for a complaint, ordered chronologically."""
        try:
            response = (
                self.client.table("status_history")
                .select("*, profiles:changed_by(full_name)")
                .eq("complaint_id", complaint_id)
                .order("created_at", desc=False)
                .execute()
            )
            results = []
            for item in response.data or []:
                prof = item.get("profiles") or {}
                item["changed_by_name"] = prof.get("full_name") if isinstance(prof, dict) else None
                results.append(item)
            return results
        except Exception as e:
            logger.error(f"Error fetching history for complaint {complaint_id}: {str(e)}")
            raise

