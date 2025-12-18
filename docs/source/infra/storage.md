# 📦 Infrastructure: Storage

> **File storage infrastructure with Supabase implementation**

This module provides file storage abstraction and concrete implementation using Supabase Storage.

---

## 📍 Location

**Directory:** `src/infra/storage/`

**Files:**
- `base.py` - StorageClient Protocol (abstraction)
- `supabase.py` - SupabaseStorageClient implementation
- `__init__.py` - Public exports

---

## 🔌 Components

### Storage Protocol

**Location:** `src/infra/storage/base.py`

Abstract interface for storage clients.

```python
from typing import Protocol, Optional

class StorageClient(Protocol):
    """Abstract storage interface."""
    
    def ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist."""
        ...
    
    def build_path(self, tender_id: str, lot_id: Optional[str], filename: str) -> str:
        """Build hierarchical storage path."""
        ...
    
    def upload_bytes(self, path: str, data: bytes, content_type: Optional[str] = None) -> None:
        """Upload file data."""
        ...
    
    def download_bytes(self, path: str) -> bytes:
        """Download file data."""
        ...
    
    def delete(self, path: str) -> None:
        """Delete file."""
        ...
```

---

### Supabase Storage Client

**Location:** `src/infra/storage/supabase.py`

Production-ready Supabase storage implementation.

```python
from src.infra.storage import get_storage_client

# Get configured client
storage = get_storage_client()

# Upload file
storage.upload_bytes(
    path="tenders/123/documents/file.pdf",
    data=pdf_bytes,
    content_type="application/pdf"
)

# Download file
data = storage.download_bytes("tenders/123/documents/file.pdf")

# Delete file
storage.delete("tenders/123/documents/file.pdf")
```

**Features:**
- ✅ Thread-safe bucket creation with double-checked locking
- ✅ Hierarchical path building (tenders/{id}/lots/{id}/documents/{file})
- ✅ Automatic bucket initialization
- ✅ Content-type support
- ✅ Exception handling (raises `StorageException` on errors)

---

## 🎯 Configuration

### Environment Variables

```bash
# .env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key  # Optional, for admin ops
STORAGE_BUCKET=tender-documents
```

### Settings

```python
# configs/config.py
from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: SecretStr
    SUPABASE_SERVICE_ROLE_KEY: SecretStr | None = None
    STORAGE_BUCKET: str
```

---

## 🚀 Usage Examples

### Upload Document in Service

```python
# src/domain/tender/services/documents.py
from uuid import uuid4
from src.infra.storage import get_storage_client

class DocumentService:
    @staticmethod
    async def create_with_upload(
        db: AsyncSession,
        data: DocumentCreate,
        file_bytes: bytes,
        content_type: str,
    ) -> Document:
        storage = get_storage_client()
        storage.ensure_bucket()
        
        # Build unique path
        unique_filename = f"{uuid4().hex}_{data.filename}"
        storage_path = storage.build_path(
            tender_id=str(data.tender_id),
            lot_id=str(data.lot_id) if data.lot_id else None,
            filename=unique_filename
        )
        
        # Upload to storage
        storage.upload_bytes(storage_path, file_bytes, content_type)
        
        # Save metadata to database
        document = Document(
            tender_id=data.tender_id,
            lot_id=data.lot_id,
            filename=data.filename,
            storage_bucket=storage.bucket_name,
            storage_path=storage_path,
        )
        db.add(document)
        await db.commit()
        return document
```

### Download in API

```python
# src/api/routers/documents.py
from fastapi import APIRouter, Response
from src.infra.storage import get_storage_client

router = APIRouter()

@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # Get document metadata
    doc = await DocumentService.get_by_id(db, document_id)
    if not doc or not doc.storage_path:
        raise HTTPException(404, "Document not found")
    
    # Download from storage
    storage = get_storage_client()
    file_bytes = storage.download_bytes(doc.storage_path)
    
    return Response(
        content=file_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={doc.filename}"}
    )
```

---

## 🗂️ Path Structure

The `build_path()` method creates a hierarchical structure:

```
tender-documents/                    # Bucket
├── tenders/
│   ├── {tender_id_1}/
│   │   ├── documents/
│   │   │   ├── abc123_bando.pdf
│   │   │   └── def456_capitolato.pdf
│   │   └── lots/
│   │       └── {lot_id_1}/
│   │           └── documents/
│   │               └── ghi789_scheda.pdf
│   └── {tender_id_2}/
│       └── documents/
│           └── jkl012_avviso.pdf
```

**Path Format:**
- Without lot: `tenders/{tender_id}/documents/{filename}`
- With lot: `tenders/{tender_id}/lots/{lot_id}/documents/{filename}`

---

## 🔄 Migration from Old Structure

**Before (Wrong):**
```python
# ❌ Storage logic in domain layer
from src.domain.tender.services.storage import get_storage_manager

storage = get_storage_manager()  # Domain-specific!
```

**After (Correct):**
```python
# ✅ Storage in infrastructure layer
from src.infra.storage import get_storage_client

storage = get_storage_client()  # Generic, reusable!
```

**Why?**
- Storage is **infrastructure concern** (not business logic)
- Easy to swap providers (Supabase → S3 → MinIO) without touching domain
- Follows Dependency Inversion Principle

---

## 🛠️ Adding New Storage Provider

To add S3, MinIO, or other providers:

### 1. Create Implementation

```python
# src/infra/storage/s3.py
import boto3
from typing import Optional

class S3StorageClient:
    """AWS S3 storage implementation."""
    
    def __init__(self, bucket_name: str, region: str, **kwargs):
        self.bucket_name = bucket_name
        self.s3 = boto3.client('s3', region_name=region, **kwargs)
    
    def ensure_bucket(self) -> None:
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
        except:
            self.s3.create_bucket(Bucket=self.bucket_name)
    
    def upload_bytes(self, path: str, data: bytes, content_type: Optional[str] = None) -> None:
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=path,
            Body=data,
            ContentType=content_type or 'application/octet-stream'
        )
    
    def download_bytes(self, path: str) -> bytes:
        obj = self.s3.get_object(Bucket=self.bucket_name, Key=path)
        return obj['Body'].read()
    
    def delete(self, path: str) -> None:
        self.s3.delete_object(Bucket=self.bucket_name, Key=path)
    
    # Implement other Protocol methods...
```

### 2. Update Factory

```python
# src/infra/storage/__init__.py
def get_storage_client(provider: str = "supabase") -> StorageClient:
    """Factory for storage clients."""
    if provider == "supabase":
        return get_supabase_client()
    elif provider == "s3":
        return S3StorageClient(
            bucket_name=settings.S3_BUCKET,
            region=settings.AWS_REGION,
        )
    else:
        raise ValueError(f"Unknown storage provider: {provider}")
```

### 3. No Domain Changes Needed!

```python
# Domain code remains unchanged
storage = get_storage_client()  # Works with any provider!
```

---

## 🧪 Testing

### Mock Storage Client

```python
# tests/test_storage.py
from unittest.mock import Mock

def test_upload_document():
    # Mock storage
    mock_storage = Mock()
    mock_storage.bucket_name = "test-bucket"
    mock_storage.upload_bytes.return_value = None
    
    # Test upload logic
    service = DocumentService()
    # ... test with mock_storage
    
    mock_storage.upload_bytes.assert_called_once()
```

### In-Memory Storage

```python
# tests/fixtures/storage.py
class InMemoryStorageClient:
    """In-memory storage for testing."""
    
    def __init__(self):
        self._files: dict[str, bytes] = {}
    
    def upload_bytes(self, path: str, data: bytes, content_type=None):
        self._files[path] = data
    
    def download_bytes(self, path: str) -> bytes:
        if path not in self._files:
            raise KeyError(f"File not found: {path}")
        return self._files[path]
    
    def delete(self, path: str):
        self._files.pop(path, None)
```

---

## 📚 See Also

- [Database Infrastructure](database.md) - SQLAlchemy setup
- [Document Service](../domain/services.md) - Using storage in services
- [Supabase Documentation](https://supabase.com/docs/guides/storage) - Official docs
- [Architecture Overview](../architecture/overview.md) - Infrastructure layer principles
