import logging
from typing import List, Optional, Dict, Any
from supabase import Client
from app.database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class DepartmentRepository:
    """Repository handling operations on departments, categories, and routing mappings."""

    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()

    def get_all_departments(self) -> List[Dict[str, Any]]:
        """Retrieve all hospital departments."""
        try:
            response = self.client.table("departments").select("*").order("name").execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching departments: {str(e)}")
            raise

    def get_department_by_id(self, department_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific department by its UUID."""
        try:
            response = self.client.table("departments").select("*").eq("id", department_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching department {department_id}: {str(e)}")
            raise

    def get_department_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific department by its case-insensitive name."""
        try:
            response = self.client.table("departments").select("*").ilike("name", name).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching department by name '{name}': {str(e)}")
            raise

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Retrieve all complaint classification categories."""
        try:
            response = self.client.table("complaint_categories").select("*").order("name").execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            raise

    def get_category_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific category by its UUID."""
        try:
            response = self.client.table("complaint_categories").select("*").eq("id", category_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching category {category_id}: {str(e)}")
            raise

    def get_department_for_category(self, category_id: str) -> Optional[str]:
        """
        AI Routing Helper:
        Finds the mapped department_id for a given category_id from department_mapping table.
        """
        try:
            response = (
                self.client.table("department_mapping")
                .select("department_id")
                .eq("category_id", category_id)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0]["department_id"]
            return None
        except Exception as e:
            logger.error(f"Error finding department for category {category_id}: {str(e)}")
            raise

    def get_all_mappings(self) -> List[Dict[str, Any]]:
        """Retrieve all category-to-department mappings with joined names."""
        try:
            response = (
                self.client.table("department_mapping")
                .select("id, category_id, department_id, created_at, complaint_categories(name), departments(name)")
                .execute()
            )
            # Flatten join format for easier consumer consumption
            results = []
            for item in response.data or []:
                cat = item.get("complaint_categories") or {}
                dept = item.get("departments") or {}
                results.append({
                    "id": item["id"],
                    "category_id": item["category_id"],
                    "department_id": item["department_id"],
                    "created_at": item["created_at"],
                    "category_name": cat.get("name") if isinstance(cat, dict) else None,
                    "department_name": dept.get("name") if isinstance(dept, dict) else None,
                })
            return results
        except Exception as e:
            logger.error(f"Error fetching department mappings: {str(e)}")
            raise

    def create_department(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new department record."""
        try:
            payload = {"name": name, "description": description}
            response = self.client.table("departments").insert(payload).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating department '{name}': {str(e)}")
            raise

