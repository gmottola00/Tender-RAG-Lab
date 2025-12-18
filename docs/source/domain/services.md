# 🏢 Domain: Services

> **Business logic and workflows for tender management**

Domain services encapsulate business operations and complex workflows.

---

## 📍 Location

**Directory:** `src/services/`

**Files:**
- `tenders.py` - Tender CRUD and workflows
- `lots.py` - Lot management
- `documents.py` - Document upload/processing
- `storage.py` - File storage abstraction

---

## 🎯 Purpose

**What services do:**
- Encapsulate business logic
- Orchestrate multiple entities
- Enforce business rules
- Provide transaction boundaries
- Reusable across apps (API, CLI, batch)

**Services bridge domain and infrastructure:**
- Use core abstractions (protocols)
- Work with domain entities (ORM models)
- Independent of HTTP/API concerns

---

## 📦 Key Services

### TenderService

**Location:** `src/services/tenders.py`

**Responsibilities:**
- CRUD operations for tenders
- Business validation (CIG format, budget limits)
- Status transitions (draft → published → archived)
- Duplicate detection

**Key methods:**

| Method | Purpose | Business Rules |
|--------|---------|----------------|
| `create_tender()` | Create new tender | Validate CIG, check duplicates |
| `update_tender()` | Update existing tender | Only drafts can be edited |
| `publish_tender()` | Publish tender | Must be draft, all fields required |
| `archive_tender()` | Archive tender | Can't archive active tenders |
| `get_by_cig()` | Find by CIG code | - |
| `list_tenders()` | Paginated list | Support filters (status, date range) |

**Example:**
```python
from src.services.tenders import TenderService

async with async_session() as session:
    service = TenderService(session)
    
    # Create with validation
    tender = await service.create_tender(
        cig="1234567890",
        title="IT Infrastructure Modernization",
        description="...",
        budget=750000.0,
        deadline="2026-03-31"
    )
    
    # Business workflow
    await service.publish_tender(tender.id)
```

---

### LotService

**Location:** `src/services/lots.py`

**Responsibilities:**
- CRUD operations for lots
- Associate lots with tenders
- Lot-specific validation
- Budget allocation (sum of lots ≤ tender budget)

**Key methods:**

| Method | Purpose | Business Rules |
|--------|---------|----------------|
| `create_lot()` | Create lot for tender | Budget ≤ remaining tender budget |
| `update_lot()` | Update lot | Can't change tender_id |
| `delete_lot()` | Delete lot | Only if no documents attached |
| `list_lots_for_tender()` | Get all lots | Ordered by index |

**Example:**
```python
from src.services.lots import LotService

service = LotService(session)

# Create lot with budget validation
lot = await service.create_lot(
    tender_id=tender.id,
    index=1,
    title="Backend Infrastructure",
    description="...",
    budget=300000.0  # Validates against tender.budget
)
```

---

### DocumentService

**Location:** `src/services/documents.py`

**Responsibilities:**
- Upload documents to storage (Supabase)
- Extract metadata (filename, size, mime type)
- Link documents to tenders/lots
- Download document URLs
- Delete documents

**Key methods:**

| Method | Purpose | Dependencies |
|--------|---------|-------------|
| `upload_document()` | Upload file to storage | `StorageClient` (core protocol) |
| `get_document()` | Get document metadata | SQLAlchemy session |
| `get_download_url()` | Generate signed URL | Storage client |
| `delete_document()` | Remove from storage + DB | Storage client + session |

**Example:**
```python
from src.services.documents import DocumentService
from fastapi import UploadFile

service = DocumentService(
    session=session,
    storage_client=get_storage_client()
)

# Upload file
document = await service.upload_document(
    file=UploadFile(...),
    tender_id=tender.id,
    lot_id=lot.id  # Optional
)

# Get download URL
url = await service.get_download_url(document.id)
```

---

### StorageService

**Location:** `src/services/storage.py`

**Responsibilities:**
- Abstract file storage operations
- Support multiple backends (Supabase, S3, local)
- Generate signed URLs
- Handle file metadata

**Key methods:**

| Method | Purpose |
|--------|---------|
| `upload()` | Upload file to storage |
| `download()` | Download file from storage |
| `delete()` | Delete file |
| `generate_signed_url()` | Temporary download URL |

**Example:**
```python
from src.infra.storage import get_storage_client, SupabaseStorageClient

storage = StorageService(supabase_client)

# Upload
file_path = await storage.upload(
    file=file_bytes,
    filename="tender-123.pdf",
    content_type="application/pdf"
)

# Generate 1-hour download URL
url = await storage.generate_signed_url(file_path, expires_in=3600)
```

---

## 🏗️ Service Patterns

### Pattern 1: Transaction Management

**Services manage database transactions:**

```python
class TenderService:
    async def create_tender(self, **data) -> Tender:
        """Create tender (atomic transaction)"""
        # Validation
        self._validate_cig(data["cig"])
        
        # Create entity
        tender = Tender(**data)
        self._session.add(tender)
        
        # Commit (or rollback on error)
        await self._session.commit()
        await self._session.refresh(tender)
        
        return tender
```

**Benefits:**
- Atomic operations
- Automatic rollback on error
- Clear transaction boundaries

---

### Pattern 2: Business Rule Enforcement

**Services enforce domain rules:**

```python
class TenderService:
    async def publish_tender(self, tender_id: int) -> Tender:
        """Publish tender with business validation"""
        tender = await self.get_by_id(tender_id)
        
        # Rule 1: Only drafts can be published
        if tender.status != "draft":
            raise ValueError(
                f"Cannot publish tender with status: {tender.status}"
            )
        
        # Rule 2: Must have required fields
        if not tender.description or not tender.deadline:
            raise ValueError("Missing required fields for publication")
        
        # Rule 3: Deadline must be in future
        if tender.deadline < datetime.utcnow().date():
            raise ValueError("Deadline must be in the future")
        
        # Apply transition
        tender.status = "published"
        tender.published_at = datetime.utcnow()
        
        await self._session.commit()
        return tender
```

---

### Pattern 3: Cross-Entity Operations

**Services coordinate multiple entities:**

```python
class TenderService:
    async def delete_tender(self, tender_id: int) -> None:
        """Delete tender and cascade to related entities"""
        tender = await self.get_by_id(tender_id)
        
        # Delete related documents first
        for doc in tender.documents:
            await self._storage.delete(doc.file_path)
            await self._session.delete(doc)
        
        # Delete related lots
        for lot in tender.lots:
            await self._session.delete(lot)
        
        # Delete tender
        await self._session.delete(tender)
        
        await self._session.commit()
```

---

### Pattern 4: Query Abstraction

**Services encapsulate complex queries:**

```python
class TenderService:
    async def search_tenders(
        self,
        query: str | None = None,
        status: str | None = None,
        min_budget: float | None = None,
        max_budget: float | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Tender]:
        """Search tenders with multiple filters"""
        stmt = select(Tender)
        
        # Text search
        if query:
            stmt = stmt.where(
                or_(
                    Tender.title.ilike(f"%{query}%"),
                    Tender.description.ilike(f"%{query}%"),
                    Tender.cig.ilike(f"%{query}%")
                )
            )
        
        # Status filter
        if status:
            stmt = stmt.where(Tender.status == status)
        
        # Budget range
        if min_budget:
            stmt = stmt.where(Tender.budget >= min_budget)
        if max_budget:
            stmt = stmt.where(Tender.budget <= max_budget)
        
        # Pagination
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self._session.execute(stmt)
        return result.scalars().all()
```

---

## 🎯 Best Practices

### 1. Validate Early

**Validate inputs before hitting database:**

```python
class TenderService:
    def _validate_cig(self, cig: str) -> None:
        """Validate CIG format (10 digits)"""
        if not cig or len(cig) != 10 or not cig.isdigit():
            raise ValueError("CIG must be 10 digits")
    
    async def create_tender(self, **data) -> Tender:
        # Validate first (fast fail)
        self._validate_cig(data["cig"])
        
        # Then DB operations
        tender = Tender(**data)
        # ...
```

---

### 2. Use Type Hints

**Always annotate types:**

```python
class TenderService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    
    async def get_by_id(self, tender_id: int) -> Tender | None:
        """Get tender by ID, returns None if not found"""
        result = await self._session.execute(
            select(Tender).where(Tender.id == tender_id)
        )
        return result.scalar_one_or_none()
```

---

### 3. Return Entities, Not Dicts

**Services return ORM entities:**

```python
# ✅ Good - return entity
async def create_tender(self, **data) -> Tender:
    tender = Tender(**data)
    self._session.add(tender)
    await self._session.commit()
    return tender  # Entity

# ❌ Bad - return dict
async def create_tender(self, **data) -> dict:
    tender = Tender(**data)
    self._session.add(tender)
    await self._session.commit()
    return {"id": tender.id, "title": tender.title}  # Lose type safety
```

**Why?** Type safety, relationship loading, validation.

---

### 4. Separate Commands and Queries

**CQRS-lite pattern:**

```python
class TenderService:
    # Commands (modify state)
    async def create_tender(self, **data) -> Tender: ...
    async def update_tender(self, tender_id: int, **data) -> Tender: ...
    async def delete_tender(self, tender_id: int) -> None: ...
    
    # Queries (read-only)
    async def get_by_id(self, tender_id: int) -> Tender | None: ...
    async def list_tenders(self, **filters) -> list[Tender]: ...
    async def count_tenders(self, **filters) -> int: ...
```

---

## 🐛 Common Issues

### Issue: N+1 Query Problem

**Symptom:** Slow list operations (many DB queries)

**Bad:**
```python
# List tenders
tenders = await service.list_tenders(limit=100)

# Access lots (triggers 100 queries!)
for tender in tenders:
    print(tender.lots)  # N+1 problem
```

**Solution:** Eager loading

```python
class TenderService:
    async def list_tenders_with_lots(self, **filters) -> list[Tender]:
        """Load tenders with lots (eager loading)"""
        stmt = select(Tender).options(
            selectinload(Tender.lots)  # Eager load
        )
        
        result = await self._session.execute(stmt)
        return result.scalars().all()
```

---

### Issue: Forgotten Commits

**Symptom:** Changes not persisted

**Bad:**
```python
async def update_tender(self, tender_id: int, **data):
    tender = await self.get_by_id(tender_id)
    for key, value in data.items():
        setattr(tender, key, value)
    # ❌ Forgot commit!
```

**Good:**
```python
async def update_tender(self, tender_id: int, **data):
    tender = await self.get_by_id(tender_id)
    for key, value in data.items():
        setattr(tender, key, value)
    await self._session.commit()  # ✅
    return tender
```

---

### Issue: Leaking DB Sessions

**Symptom:** Connection pool exhaustion

**Bad:**
```python
# Global session (never closed!)
session = async_session()
service = TenderService(session)
```

**Good:**
```python
# Context manager (auto-closes)
async with async_session() as session:
    service = TenderService(session)
    tender = await service.create_tender(...)
# Session closed here
```

---

## 📚 Related Documentation

- [Domain Layer Overview](README.md)
- [Domain Entities](entities.md) - ORM models
- [Apps: API Endpoints](../apps/api-endpoints.md) - How services are used
- [Core: RAG](../core/rag.md) - Document processing

---

**[⬅️ Domain README](README.md) | [⬆️ Documentation Home](../README.md)**

*Last updated: 2025-12-18*
