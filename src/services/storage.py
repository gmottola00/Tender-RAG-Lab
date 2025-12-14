from __future__ import annotations

import threading
from typing import Optional

from supabase import Client, create_client

from configs.config import settings


class SupabaseStorageManager:
    """Lightweight manager to ensure a bucket exists and generate storage paths."""

    def __init__(self, bucket_name: str, url: str, api_key: str, public: bool = False) -> None:
        if not bucket_name:
            raise ValueError("bucket_name is required")
        self.bucket_name = bucket_name
        self.public = public
        self._client: Client = create_client(url, api_key)
        self._bucket_checked = False
        self._lock = threading.Lock()

    def ensure_bucket(self) -> None:
        """Create the bucket if it does not exist."""
        if self._bucket_checked:
            return
        with self._lock:
            if self._bucket_checked:
                return
            existing = {b.name for b in (self._client.storage.list_buckets() or [])}
            if self.bucket_name not in existing:
                # public=False keeps documents private; adjust if you want public access.
                self._client.storage.create_bucket(self.bucket_name, {"public": self.public})
            self._bucket_checked = True

    def build_path(self, tender_id: str, lot_id: Optional[str], filename: str) -> str:
        """Build a storage path grouping by tender and lot."""
        parts = ["tenders", str(tender_id)]
        if lot_id:
            parts.append(f"lots/{lot_id}")
        parts.append("documents")
        parts.append(filename)
        return "/".join(parts)

    def upload_bytes(self, path: str, data: bytes, content_type: Optional[str] = None) -> None:
        """Upload raw bytes to the configured bucket."""
        self.ensure_bucket()
        options = {}
        if content_type:
            options["contentType"] = content_type
        # Raises a StorageException on errors; let it bubble up.
        self._client.storage.from_(self.bucket_name).upload(path, data, options)

    def download_bytes(self, path: str) -> bytes:
        """Download raw bytes from the configured bucket."""
        self.ensure_bucket()
        # Returns bytes or raises StorageException
        return self._client.storage.from_(self.bucket_name).download(path)


def get_storage_manager() -> SupabaseStorageManager:
    """Factory for a reusable storage manager."""
    bucket = settings.STORAGE_BUCKET
    if not bucket:
        raise RuntimeError("STORAGE_BUCKET env variable is required")
    api_key = (
        settings.SUPABASE_SERVICE_ROLE_KEY.get_secret_value()
        if settings.SUPABASE_SERVICE_ROLE_KEY
        else settings.SUPABASE_KEY.get_secret_value()
    )
    return SupabaseStorageManager(bucket_name=bucket, url=settings.SUPABASE_URL, api_key=api_key, public=False)
