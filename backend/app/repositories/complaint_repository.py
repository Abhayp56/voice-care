import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from supabase import Client
from app.database.supabase_client import get_supabase_client
from app.models.complaint import ComplaintStatus, ComplaintPriority

logger = logging.getLogger(__name__)


class ComplaintRepository:
    """Repository handling all CRUD and search operations on complaints table."""

    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()

    def generate_next_complaint_number(self) -> str:
        """
        Generates the next sequential human-readable complaint number (e.g. VC-2026-0006)
        using the atomic `next_complaint_number` database function.
        """
        current_year = datetime.now(timezone.utc).year
        try:
            result = self.client.rpc("next_complaint_number", {"p_year": current_year}).execute()
            next_number = result.data
            if isinstance(next_number, list):
                next_number = next_number[0] if next_number else None
            if isinstance(next_number, dict):
                next_number = next_number.get("next_complaint_number")
            if not isinstance(next_number, int) or next_number < 1:
                raise RuntimeError("Atomic complaint number function returned an invalid value.")
            return f"VC-{current_year}-{next_number:04d}"
        except Exception as e:
            logger.error(f"Error generating complaint number: {str(e)}")
            raise RuntimeError("Could not allocate a unique complaint number.") from e

    def create_complaint(
        self,
        description: str,
        category_id: str,
        department_id: str,
        patient_name: Optional[str] = None,
        patient_phone: Optional[str] = None,
        language: str = "en",
        priority: str = "medium",
        status: str = "received",
        complaint_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new complaint record with auto-generated tracking number."""
        if not complaint_number:
            complaint_number = self.generate_next_complaint_number()

        payload = {
            "complaint_number": complaint_number,
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "description": description,
            "language": language,
            "category_id": category_id,
            "department_id": department_id,
            "priority": priority,
            "status": status,
        }

        try:
            response = self.client.table("complaints").insert(payload).execute()
            if not response.data:
                raise RuntimeError("Failed to insert complaint into database.")
            created = response.data[0]
            logger.info(f"Complaint created successfully: {created.get('complaint_number')}")
            return created
        except Exception as e:
            logger.error(f"Error inserting complaint: {str(e)}")
            raise

    def get_complaint_by_id(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a complaint by its UUID or its human-readable complaint_number.
        Joins department and category details.
        """
        try:
            query = self.client.table("complaints").select(
                "*, departments(name), complaint_categories(name), profiles:assigned_to(full_name)"
            )
            # Check if UUID or complaint_number format (VC-YYYY-NNNN)
            if complaint_id.startswith("VC-"):
                query = query.eq("complaint_number", complaint_id)
            else:
                query = query.eq("id", complaint_id)

            response = query.execute()
            if not response.data:
                return None

            data = response.data[0]
            dept = data.get("departments") or {}
            cat = data.get("complaint_categories") or {}
            prof = data.get("profiles") or {}

            data["department_name"] = dept.get("name") if isinstance(dept, dict) else None
            data["category_name"] = cat.get("name") if isinstance(cat, dict) else None
            data["assigned_to_name"] = prof.get("full_name") if isinstance(prof, dict) else None
            return data
        except Exception as e:
            logger.error(f"Error retrieving complaint {complaint_id}: {str(e)}")
            raise

    def get_complaints(
        self,
        department_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        search_query: Optional[str] = None,
        older_than_days: Optional[int] = None,
        open_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve paginated complaints with flexible filtering.
        Returns (list_of_complaints, total_count).
        """
        try:
            query = self.client.table("complaints").select(
                "*, departments(name), complaint_categories(name), profiles:assigned_to(full_name)",
                count="exact"
            )

            if department_id:
                query = query.eq("department_id", department_id)
            if status:
                query = query.eq("status", status)
            if priority:
                query = query.eq("priority", priority)
            if category_id:
                query = query.eq("category_id", category_id)
            if assigned_to:
                query = query.eq("assigned_to", assigned_to)
            if open_only:
                query = query.neq("status", "resolved").neq("status", "closed")
            if older_than_days is not None:
                cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
                query = query.lte("created_at", cutoff.isoformat())
            if search_query:
                # Search within description, patient_name or complaint_number
                query = query.ilike("description", f"%{search_query}%")

            response = (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            total_count = response.count if response.count is not None else len(response.data)

            results = []
            for item in response.data or []:
                dept = item.get("departments") or {}
                cat = item.get("complaint_categories") or {}
                prof = item.get("profiles") or {}
                item["department_name"] = dept.get("name") if isinstance(dept, dict) else None
                item["category_name"] = cat.get("name") if isinstance(cat, dict) else None
                item["assigned_to_name"] = prof.get("full_name") if isinstance(prof, dict) else None
                results.append(item)

            return results, total_count
        except Exception as e:
            logger.error(f"Error querying complaints: {str(e)}")
            raise

    def get_complaints_by_department(
        self,
        department_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Retrieve complaints for a specific department."""
        return self.get_complaints(
            department_id=department_id,
            status=status,
            limit=limit,
            offset=offset
        )

    def get_pending_complaints(
        self,
        department_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Retrieve active complaints that are received or assigned."""
        try:
            query = (
                self.client.table("complaints")
                .select("*, departments(name), complaint_categories(name)", count="exact")
                .in_("status", ["received", "assigned"])
            )
            if department_id:
                query = query.eq("department_id", department_id)

            response = (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            total = response.count if response.count is not None else len(response.data)
            return response.data or [], total
        except Exception as e:
            logger.error(f"Error fetching pending complaints: {str(e)}")
            raise

    def get_overdue_complaints(
        self,
        threshold_hours: int = 48,
        department_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve complaints that have remained unresolved longer than the SLA threshold
        (default 48 hours) or are in escalated status.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=threshold_hours)
        cutoff_iso = cutoff.isoformat()

        try:
            query = (
                self.client.table("complaints")
                .select("*, departments(name), complaint_categories(name)")
                .neq("status", "resolved")
                .neq("status", "closed")
                .lt("created_at", cutoff_iso)
            )
            if department_id:
                query = query.eq("department_id", department_id)

            response = query.order("created_at", desc=False).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching overdue complaints: {str(e)}")
            raise

    def update_complaint_status(
        self,
        complaint_id: str,
        new_status: str,
        note: Optional[str] = None,
        changed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Atomically update complaint status and append its audit history entry.
        """
        try:
            response = self.client.rpc("transition_complaint_status", {
                "p_complaint_id": complaint_id,
                "p_new_status": new_status,
                "p_changed_by": changed_by,
                "p_note": note,
            }).execute()
            updated_complaint = response.data
            if isinstance(updated_complaint, list):
                updated_complaint = updated_complaint[0] if updated_complaint else None
            if not isinstance(updated_complaint, dict):
                raise ValueError(f"Complaint with ID '{complaint_id}' does not exist or transition failed.")

            logger.info(f"Complaint {complaint_id} status updated to {new_status}")
            return updated_complaint
        except Exception as e:
            logger.error(f"Error updating complaint status for {complaint_id}: {str(e)}")
            raise

    def update_complaint(self, complaint_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Generic complaint update helper for reassigning, reprioritizing, etc."""
        try:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            res = self.client.table("complaints").update(updates).eq("id", complaint_id).execute()
            if not res.data:
                raise ValueError(f"Complaint with ID '{complaint_id}' not found.")
            return res.data[0]
        except Exception as e:
            logger.error(f"Error updating complaint {complaint_id}: {str(e)}")
            raise

