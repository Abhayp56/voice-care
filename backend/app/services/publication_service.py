import logging
from typing import List, Optional, Dict, Any, Tuple
from supabase import Client
from app.database.supabase_client import get_supabase_client
from app.models.complaint import PublicComplaintResponse
from app.models.dashboard import PublicDepartmentStatsResponse

logger = logging.getLogger(__name__)


class PublicationService:
    """
    Public Transparency Service.
    Guarantees privacy-safe data publishing by querying the database views:
    `public_complaints_view` and `public_department_statistics`.
    
    CRITICAL SECURITY ENFORCEMENT:
    Under NO circumstances will this service return patient_name, patient_phone,
    internal notes, staff assignments, or sensitive photos.
    """

    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()

    def get_public_complaints(
        self,
        department_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[PublicComplaintResponse], int]:
        """
        Fetches privacy-safe complaints from the database view `public_complaints_view`.
        Exposes complaint_number, department_name, category_name, status, and submission_date ONLY.
        """
        try:
            query = self.client.table("public_complaints_view").select("*", count="exact")

            if department_name:
                query = query.ilike("department_name", department_name)
            if status:
                query = query.eq("status", status)

            response = (
                query.range(offset, offset + limit - 1)
                .execute()
            )
            total = response.count if response.count is not None else len(response.data)
            
            clean_records = [
                PublicComplaintResponse(
                    complaint_number=row["complaint_number"],
                    department_name=row.get("department_name"),
                    category_name=row.get("category_name"),
                    status=row.get("status", "received"),
                    submission_date=str(row.get("submission_date")) if row.get("submission_date") else None
                )
                for row in response.data or []
            ]
            return clean_records, total
        except Exception as e:
            logger.error(f"Error fetching public complaints view: {str(e)}")
            raise

    def get_public_tracking_status(self, complaint_number: str) -> Optional[PublicComplaintResponse]:
        """
        Allows patients to check the current status of their complaint using their tracking number.
        Returns ONLY public status information.
        """
        try:
            response = (
                self.client.table("public_complaints_view")
                .select("*")
                .eq("complaint_number", complaint_number)
                .execute()
            )
            if not response.data:
                return None
            row = response.data[0]
            return PublicComplaintResponse(
                complaint_number=row["complaint_number"],
                department_name=row.get("department_name"),
                category_name=row.get("category_name"),
                status=row.get("status", "received"),
                submission_date=str(row.get("submission_date")) if row.get("submission_date") else None
            )
        except Exception as e:
            logger.error(f"Error tracking public complaint {complaint_number}: {str(e)}")
            raise

    def get_public_department_statistics(self) -> List[PublicDepartmentStatsResponse]:
        """
        Fetches civic transparency stats from `public_department_statistics` view.
        Returns aggregate counts per department (total, resolved, open).
        """
        try:
            response = (
                self.client.table("public_department_statistics")
                .select("*")
                .order("department_name")
                .execute()
            )
            return [
                PublicDepartmentStatsResponse(
                    department_name=row["department_name"],
                    total_complaints=row.get("total_complaints", 0),
                    resolved_count=row.get("resolved_count", 0),
                    open_count=row.get("open_count", 0),
                )
                for row in response.data or []
            ]
        except Exception as e:
            logger.error(f"Error fetching public department statistics: {str(e)}")
            raise

