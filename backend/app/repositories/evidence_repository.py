import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from supabase import Client
from app.database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class EvidenceRepository:
    """Repository handling evidence metadata records in the evidence table."""

    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()

    def create_evidence(
        self,
        complaint_id: str,
        file_path: str,
        file_type: str = "image",
        notes: Optional[str] = None,
        submitted_by: Optional[str] = None,
        gps_latitude: Optional[float] = None,
        gps_longitude: Optional[float] = None,
        gps_accuracy_m: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Record evidence upload metadata in database."""
        try:
            payload = {
                "complaint_id": complaint_id,
                "file_path": file_path,
                "file_type": file_type,
                "notes": notes,
                "submitted_by": submitted_by,
                "gps_latitude": gps_latitude,
                "gps_longitude": gps_longitude,
                "gps_accuracy_m": gps_accuracy_m,
            }
            response = self.client.table("evidence").insert(payload).execute()
            if not response.data:
                raise RuntimeError("Failed to insert evidence record.")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error inserting evidence for complaint {complaint_id}: {str(e)}")
            raise

    def get_evidence_by_id(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single evidence record with submitted and verified profile names."""
        try:
            response = (
                self.client.table("evidence")
                .select("*, submitted:submitted_by(full_name), verified:verified_by(full_name)")
                .eq("id", evidence_id)
                .execute()
            )
            if not response.data:
                return None
            data = response.data[0]
            sub = data.get("submitted") or {}
            ver = data.get("verified") or {}
            data["submitted_by_name"] = sub.get("full_name") if isinstance(sub, dict) else None
            data["verified_by_name"] = ver.get("full_name") if isinstance(ver, dict) else None
            return data
        except Exception as e:
            logger.error(f"Error retrieving evidence {evidence_id}: {str(e)}")
            raise

    def get_evidence_by_complaint(self, complaint_id: str) -> List[Dict[str, Any]]:
        """Retrieve all evidence items attached to a complaint."""
        try:
            response = (
                self.client.table("evidence")
                .select("*, submitted:submitted_by(full_name), verified:verified_by(full_name)")
                .eq("complaint_id", complaint_id)
                .order("created_at", desc=True)
                .execute()
            )
            results = []
            for item in response.data or []:
                sub = item.get("submitted") or {}
                ver = item.get("verified") or {}
                item["submitted_by_name"] = sub.get("full_name") if isinstance(sub, dict) else None
                item["verified_by_name"] = ver.get("full_name") if isinstance(ver, dict) else None
                results.append(item)
            return results
        except Exception as e:
            logger.error(f"Error retrieving evidence for complaint {complaint_id}: {str(e)}")
            raise

    def verify_evidence(
        self,
        evidence_id: str,
        verified: bool,
        verified_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a human review by a department head or hospital administrator.
        """
        try:
            updates: Dict[str, Any] = {
                "verified_by": verified_by,
                # A rejected review must never look like successful verification.
                "verified_at": datetime.now(timezone.utc).isoformat() if verified else None
            }
            if notes:
                # Append or update notes
                updates["notes"] = notes

            response = self.client.table("evidence").update(updates).eq("id", evidence_id).execute()
            if not response.data:
                raise ValueError(f"Evidence record '{evidence_id}' not found.")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error verifying evidence {evidence_id}: {str(e)}")
            raise

    def record_ai_analysis(self, evidence_id: str, complaint_id: str, actor_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Persist an advisory result separately from human verification fields."""
        response = self.client.table("ai_evidence_reviews").insert({
            "evidence_id": evidence_id,
            "complaint_id": complaint_id,
            "requested_by": actor_id,
            "result": result,
        }).execute()
        if not response.data:
            raise RuntimeError("AI evidence review could not be recorded")
        return response.data[0]

    def has_ai_analysis(self, evidence_id: str) -> bool:
        result = self.client.table("ai_evidence_reviews").select("id").eq("evidence_id", evidence_id).limit(1).execute()
        return bool(result.data)

