import logging
from typing import List, Optional, Dict, Any
from supabase import Client
from app.database.supabase_client import get_supabase_client
from app.models.user import UserRole

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository handling staff and officer profiles in the profiles table."""

    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()

    def get_profile_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile by UUID, including joined department name."""
        try:
            response = (
                self.client.table("profiles")
                .select("*, departments(name)")
                .eq("id", user_id)
                .execute()
            )
            if not response.data:
                return None
            data = response.data[0]
            dept = data.get("departments") or {}
            data["department_name"] = dept.get("name") if isinstance(dept, dict) else None
            return data
        except Exception as e:
            logger.error(f"Error fetching profile for user {user_id}: {str(e)}")
            raise

    def get_profiles_by_department(self, department_id: str) -> List[Dict[str, Any]]:
        """Retrieve all staff profiles belonging to a department."""
        try:
            response = (
                self.client.table("profiles")
                .select("*, departments(name)")
                .eq("department_id", department_id)
                .order("full_name")
                .execute()
            )
            results = []
            for item in response.data or []:
                dept = item.get("departments") or {}
                item["department_name"] = dept.get("name") if isinstance(dept, dict) else None
                results.append(item)
            return results
        except Exception as e:
            logger.error(f"Error fetching profiles for department {department_id}: {str(e)}")
            raise

    def list_profiles(
        self,
        role: Optional[UserRole] = None,
        department_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List profiles with optional filtering by role or department."""
        try:
            query = self.client.table("profiles").select("*, departments(name)")
            if role:
                query = query.eq("role", role.value if hasattr(role, "value") else role)
            if department_id:
                query = query.eq("department_id", department_id)
            response = query.order("created_at", desc=True).execute()

            results = []
            for item in response.data or []:
                dept = item.get("departments") or {}
                item["department_name"] = dept.get("name") if isinstance(dept, dict) else None
                results.append(item)
            return results
        except Exception as e:
            logger.error(f"Error listing profiles: {str(e)}")
            raise

    def create_or_update_profile(
        self,
        user_id: str,
        full_name: str,
        role: str = "department_staff",
        department_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update a profile linked to Supabase Auth."""
        try:
            payload = {
                "id": user_id,
                "full_name": full_name,
                "role": role,
                "department_id": department_id
            }
            response = self.client.table("profiles").upsert(payload).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating/updating profile for user {user_id}: {str(e)}")
            raise

