import os
import uuid
import logging
from typing import Optional, Dict, Any, Tuple
from fastapi import UploadFile, HTTPException, status
from supabase import Client
from app.config import settings
from app.database.supabase_client import get_supabase_client
from app.repositories.evidence_repository import EvidenceRepository

logger = logging.getLogger(__name__)


class StorageService:
    """
    Manages resolution evidence uploads, validations, and signed URL generation
    utilizing the existing private 'evidence' Supabase Storage bucket.
    """

    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()
        self.bucket_name = settings.SUPABASE_STORAGE_BUCKET
        self.evidence_repo = EvidenceRepository(self.client)

    def validate_file(self, filename: str, content_type: str, file_size: int, content: Optional[bytes] = None) -> None:
        """
        Validates evidence file against allowed MIME types and file size limit (5MB).
        """
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE if hasattr(status, "HTTP_413_CONTENT_TOO_LARGE") else 413,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB.",
            )

        if content_type not in settings.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type '{content_type}'. Allowed types: {', '.join(settings.ALLOWED_MIME_TYPES)}.",
            )

        if content is not None and self._detect_image_type(content) != content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match its declared image type.",
            )

    @staticmethod
    def _detect_image_type(content: bytes) -> Optional[str]:
        if content.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
            return "image/webp"
        return None

    def generate_storage_path(self, complaint_id: str, original_filename: str, content_type: Optional[str] = None) -> str:
        """
        Generates safe, unique namespaced storage path:
        Format: complaints/{complaint_id}/{unique_id}_{clean_filename}
        """
        ext = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }.get(content_type or "", os.path.splitext(original_filename)[1].lower())
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            ext = ".jpg"
        unique_token = uuid.uuid4().hex[:12]
        safe_name = f"{unique_token}{ext}"
        return f"{complaint_id}/{safe_name}"

    async def upload_evidence(
        self,
        complaint_id: str,
        file: UploadFile,
        notes: Optional[str] = None,
        submitted_by: Optional[str] = None,
        gps_latitude: Optional[float] = None,
        gps_longitude: Optional[float] = None,
        gps_accuracy_m: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Uploads evidence photo to private storage and logs metadata in database.
        """
        content = await file.read(settings.MAX_UPLOAD_SIZE_BYTES + 1)
        file_size = len(content)

        # 1. Validate file constraints
        self.validate_file(
            filename=file.filename or "evidence.jpg",
            content_type=file.content_type or "image/jpeg",
            file_size=file_size,
            content=content,
        )

        # 2. Generate unique storage path
        storage_path = self.generate_storage_path(
            complaint_id=complaint_id,
            original_filename=file.filename or "evidence.jpg",
            content_type=file.content_type or "image/jpeg",
        )

        # 3. Upload to Supabase Storage
        try:
            self.client.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=content,
                file_options={"content-type": file.content_type or "image/jpeg", "upsert": "false"}
            )
            logger.info(f"File uploaded to Supabase Storage: {storage_path}")
        except Exception as e:
            logger.error(f"Failed to upload file to storage: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload evidence to storage: {str(e)}"
            )

        # 4. Save metadata in `evidence` table
        try:
            evidence_record = self.evidence_repo.create_evidence(
                complaint_id=complaint_id,
                file_path=storage_path,
                file_type="image",
                notes=notes,
                submitted_by=submitted_by,
                gps_latitude=gps_latitude,
                gps_longitude=gps_longitude,
                gps_accuracy_m=gps_accuracy_m,
            )
        except Exception as exc:
            try:
                self.client.storage.from_(self.bucket_name).remove([storage_path])
            except Exception:
                logger.error("Could not remove orphaned evidence object after metadata failure")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Evidence metadata could not be saved.",
            ) from exc

        # 5. Attach a signed URL for immediate view
        signed_url = self.get_signed_url(storage_path, expires_in=3600)
        evidence_record["signed_url"] = signed_url
        return evidence_record

    def get_signed_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generates a temporary signed URL for authorized viewing of private evidence photos.
        Prevents direct public exposure of sensitive hospital photos.
        """
        try:
            res = self.client.storage.from_(self.bucket_name).create_signed_url(
                path=file_path,
                expires_in=expires_in
            )
            if isinstance(res, dict) and "signedURL" in res:
                return res["signedURL"]
            elif isinstance(res, dict) and "signedUrl" in res:
                return res["signedUrl"]
            return res.get("signedURL") if isinstance(res, dict) else str(res)
        except Exception as e:
            logger.warning(f"Could not generate signed URL for {file_path}: {str(e)}")
            return None

    def download_evidence(self, file_path: str) -> bytes:
        """Download an evidence object for an authorized backend analysis."""
        try:
            result = self.client.storage.from_(self.bucket_name).download(file_path)
            if not isinstance(result, bytes) or not result:
                raise ValueError("Evidence object is empty")
            return result
        except Exception as exc:
            logger.warning("Evidence download failed; error_type=%s", type(exc).__name__)
            raise HTTPException(status_code=503, detail="Evidence could not be loaded for analysis.") from None
