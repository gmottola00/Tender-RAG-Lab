# 🏢 Domain Layer: README

> **Business logic and domain models for tender management**

The domain layer contains business-specific logic and entity models for the tender management system.

---

## 🎯 Philosophy

**Domain principles:**

1. **Business Logic Lives Here** - Validation, workflows, domain rules
2. **Framework Independent** - No FastAPI, no HTTP concerns
3. **Reusable** - Can be used in CLI, batch jobs, or APIs
4. **Rich Models** - Entities with behavior, not just data classes

**The domain layer is:**
- Where tender-specific logic lives
- Independent of HTTP/API concerns
- Reusable across different applications (FastAPI, CLI, batch)
- Dependent on core abstractions (not implementations)

**See:** [Architecture Overview](../architecture/overview.md) for layer dependencies.

---

## 📁 Module Structure

```
src/domain/
├── models/          # Domain entities (Tender, Lot, Document)
├── services/        # Business logic services
└── schemas/         # Pydantic validation schemas
```

Related (outside domain):
```
src/
├── models/          # SQLAlchemy ORM models
└── schemas/         # API request/response schemas
```

---

## 📦 Modules Overview

### Models (Entities)

**Location:** `src/models/` (SQLAlchemy ORM)

**Purpose:** Database entities with relationships.

**Key models:**
- `Tender` - Public procurement tender
- `Lot` - Tender subdivision
- `Document` - Attached files

**Example:**
```python
from src.models.tenders import Tender

tender = Tender(
    cig="1234567890",
    title="IT Services Procurement",
    description="...",
    budget=500000.0,
    status="published"
)
```

**Note:** These are ORM models, not pure domain entities. For pure domain, see schemas.

**Read more:** [Domain Entities](entities.md)

---

### Services (Business Logic)

**Location:** `src/services/`

**Purpose:** Business operations and workflows.

**Key services:**
- `TenderService` - Tender CRUD + validation
- `LotService` - Lot management
- `DocumentService` - File upload/download
- `IngestionService` - Document processing pipeline

**Example:**
```python
from src.services.tenders import TenderService

service = TenderService(session)

# Create tender with validation
tender = await service.create_tender(
    cig="1234567890",
    title="IT Services",
    budget=500000.0
)

# Business logic (e.g., status validation)
await service.publish_tender(tender.id)
```

**Read more:** [Domain Services](services.md)

---

### Schemas (Validation)

**Location:** `src/schemas/`

**Purpose:** Request/response validation with Pydantic.

**Key schemas:**
- `TenderCreate` / `TenderRead` - Tender DTOs
- `LotCreate` / `LotRead` - Lot DTOs
- `DocumentUpload` / `DocumentRead` - Document DTOs

**Example:**
```python
from src.schemas.tenders import TenderCreate

# Validates input
tender_data = TenderCreate(
    cig="1234567890",  # Must be 10 digits
    title="IT Services",
    budget=500000.0,  # Must be positive
    deadline="2025-12-31"
)

# Raises ValidationError if invalid
```

**Read more:** [Schemas & Validation](schemas.md)

---

## 🏗️ Design Patterns

### 1. Service Layer Pattern

**Services encapsulate business logic:**

```python
# src/services/tenders.py
class TenderService:
    """Business operations for tenders"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create_tender(self, **data) -> Tender:
        """Create tender with business validation"""
        # 1. Validate CIG format
        self._validate_cig(data["cig"])
        
        # 2. Check for duplicates
        if await self._cig_exists(data["cig"]):
            raise ValueError("CIG already exists")
        
        # 3. Create entity
        tender = Tender(**data)
        self._session.add(tender)
        await self._session.commit()
        
        return tender
    
    async def publish_tender(self, tender_id: int) -> Tender:
        """Publish tender (business workflow)"""
        tender = await self._get_by_id(tender_id)
        
        # Business rule: can only publish draft tenders
        if tender.status != "draft":
            raise ValueError("Can only publish draft tenders")
        
        tender.status = "published"
        tender.published_at = datetime.utcnow()
        
        await self._session.commit()
        return tender
```

**Benefits:**
- Business logic in one place
- Reusable (CLI, API, batch)
- Testable (mock database)

---

### 2. Repository Pattern (Implicit)

**Services act as repositories:**

```python
class TenderService:
    async def get_by_id(self, tender_id: int) -> Tender:
        """Get tender by ID"""
        result = await self._session.execute(
            select(Tender).where(Tender.id == tender_id)
        )
        return result.scalar_one_or_none()
    
    async def list_tenders(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None
    ) -> list[Tender]:
        """List tenders with filters"""
        query = select(Tender)
        
        if status:
            query = query.where(Tender.status == status)
        
        query = query.offset(skip).limit(limit)
        
        result = await self._session.execute(query)
        return result.scalars().all()
```

---

### 3. Dependency Injection

**Services receive dependencies via constructor:**

```python
# src/services/documents.py
class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        storage_client: StorageClient,  # Core protocol
        parser: DocumentParser,         # Core protocol
        embedding_client: EmbeddingClient
    ):
        self._session = session
        self._storage = storage_client
        self._parser = parser
        self._embed = embedding_client
    
    async def upload_document(self, file: UploadFile, tender_id: int):
        """Upload and process document"""
        # 1. Save to storage
        url = await self._storage.upload(file)
        
        # 2. Parse text
        pages = self._parser.parse(file.filename)
        
        # 3. Embed and index
        # ...
```

**Wiring in API:**
```python
# src/api/deps.py
def get_document_service(session: AsyncSession) -> DocumentService:
    return DocumentService(
        session=session,
        storage_client=get_storage_client(),
        parser=get_document_parser(),
        embedding_client=get_embedding_client()
    )
```

---

## 🎯 Common Use Cases

### Use Case 1: Add Tender Validation Rule

**Goal:** Validate that budget is within ministry limits.

**Where:** Domain service (business logic)

```python
# src/services/tenders.py
class TenderService:
    BUDGET_LIMITS = {
        "IT": 1_000_000,
        "construction": 5_000_000,
        "services": 500_000
    }
    
    async def create_tender(self, **data) -> Tender:
        # Business validation
        category = data.get("category")
        budget = data.get("budget")
        
        max_budget = self.BUDGET_LIMITS.get(category)
        if max_budget and budget > max_budget:
            raise ValueError(
                f"Budget exceeds limit for {category}: "
                f"{budget} > {max_budget}"
            )
        
        # ... rest of creation logic
```

**Why domain?** This is a business rule, not a technical constraint.

---

### Use Case 2: Complex Workflow

**Goal:** Tender approval workflow (draft → review → approved → published).

```python
# src/services/tenders.py
class TenderService:
    async def submit_for_review(self, tender_id: int) -> Tender:
        """Submit tender for review"""
        tender = await self.get_by_id(tender_id)
        
        # Business rule: must be draft
        if tender.status != "draft":
            raise ValueError("Only draft tenders can be submitted")
        
        # Business rule: must have all required fields
        self._validate_completeness(tender)
        
        tender.status = "review"
        await self._session.commit()
        return tender
    
    async def approve_tender(self, tender_id: int, reviewer_id: int) -> Tender:
        """Approve tender (requires permissions)"""
        tender = await self.get_by_id(tender_id)
        
        if tender.status != "review":
            raise ValueError("Can only approve tenders in review")
        
        tender.status = "approved"
        tender.approved_by = reviewer_id
        tender.approved_at = datetime.utcnow()
        
        await self._session.commit()
        return tender
```

---

### Use Case 3: Cross-Entity Operations

**Goal:** Archive tender and all related entities.

```python
# src/services/tenders.py
class TenderService:
    async def archive_tender(self, tender_id: int) -> None:
        """Archive tender and related entities"""
        tender = await self.get_by_id(tender_id)
        
        # Business rule: can't archive active tenders
        if tender.status in ["published", "active"]:
            raise ValueError("Cannot archive active tender")
        
        # Archive tender
        tender.status = "archived"
        tender.archived_at = datetime.utcnow()
        
        # Archive related lots
        for lot in tender.lots:
            lot.status = "archived"
        
        # Archive related documents
        for doc in tender.documents:
            doc.status = "archived"
        
        await self._session.commit()
```

---

## 🎓 Learning Path

### For New Contributors

**Start here:**
1. [Architecture Overview](../architecture/overview.md) - Layer structure
2. [Where to Put Code](../architecture/where-to-put-code.md) - Domain vs apps
3. [Domain Entities](entities.md) - Understand models
4. [Domain Services](services.md) - Business logic patterns

### For Adding Features

**Focus on:**
- Identify if logic is business or technical
- Business → domain services
- API contracts → schemas
- Database → models (ORM)

---

## 🐛 Common Mistakes

### ❌ HTTP Logic in Domain

**Bad:**
```python
# src/services/tenders.py
from fastapi import HTTPException  # ❌

class TenderService:
    async def create_tender(self, **data):
        if not data.get("cig"):
            raise HTTPException(status_code=400, detail="CIG required")  # ❌
```

**Good:**
```python
# src/services/tenders.py
class TenderService:
    async def create_tender(self, **data):
        if not data.get("cig"):
            raise ValueError("CIG required")  # ✅ Domain exception

# src/api/routers/tenders.py (Apps layer)
try:
    tender = await service.create_tender(**data)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))  # ✅ HTTP here
```

---

### ❌ Database Queries in API Routers

**Bad:**
```python
# src/api/routers/tenders.py
@router.get("/tenders/{tender_id}")
async def get_tender(tender_id: int, session: AsyncSession):
    result = await session.execute(  # ❌ DB query in router
        select(Tender).where(Tender.id == tender_id)
    )
    return result.scalar_one()
```

**Good:**
```python
# src/services/tenders.py
class TenderService:
    async def get_by_id(self, tender_id: int) -> Tender:  # ✅
        result = await self._session.execute(
            select(Tender).where(Tender.id == tender_id)
        )
        return result.scalar_one_or_none()

# src/api/routers/tenders.py
@router.get("/tenders/{tender_id}")
async def get_tender(
    tender_id: int,
    service: TenderService = Depends(get_tender_service)
):
    return await service.get_by_id(tender_id)  # ✅
```

---

### ❌ Business Logic in Models

**Bad:**
```python
# src/models/tenders.py
class Tender(Base):
    # ... fields ...
    
    def publish(self):  # ❌ Business logic in ORM model
        if self.status != "draft":
            raise ValueError("Can only publish drafts")
        self.status = "published"
```

**Good:**
```python
# src/models/tenders.py
class Tender(Base):
    # ... fields only ...

# src/services/tenders.py
class TenderService:
    async def publish_tender(self, tender_id: int):  # ✅
        tender = await self.get_by_id(tender_id)
        if tender.status != "draft":
            raise ValueError("Can only publish drafts")
        tender.status = "published"
        await self._session.commit()
```

---

## 📚 Related Documentation

- [Architecture Overview](../architecture/overview.md) - Layer dependencies
- [Core Layer](../core/README.md) - Reusable abstractions
- [Apps Layer](../apps/README.md) - API implementation
- [Where to Put Code](../architecture/where-to-put-code.md) - Decision guide

---

**[⬆️ Documentation Home](../README.md) | [Domain Entities ➡️](entities.md)**

*Last updated: 2025-12-18*
