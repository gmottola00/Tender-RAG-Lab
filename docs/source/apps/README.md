# 🌐 Apps Layer: README

> **HTTP API layer: FastAPI routes and dependency injection**

The apps layer contains HTTP-specific code: API endpoints, request/response handling, and authentication.

---

## 🎯 Philosophy

**Apps principles:**

1. **Thin Layer** - Minimal logic, delegate to domain services
2. **HTTP Concerns Only** - Request parsing, response formatting, status codes
3. **Framework-Specific** - FastAPI dependencies, middleware, etc.
4. **Validation at Boundary** - Pydantic schemas for input/output

**The apps layer is:**
- Where HTTP/REST lives
- Dependent on domain services (business logic)
- Framework-specific (FastAPI)
- Stateless (no business logic)

**See:** [Architecture Overview](../architecture/overview.md) for layer dependencies.

---

## 📁 Module Structure

```
src/api/
├── routers/           # API endpoint modules
│   ├── tenders.py     # /api/tenders endpoints
│   ├── lots.py        # /api/lots endpoints
│   ├── documents.py   # /api/documents endpoints
│   ├── ingestion.py   # /api/ingestion endpoints
│   └── ui.py          # /demo, /home HTML routes
├── deps.py            # Dependency injection
├── auth.py            # Authentication (future)
└── providers.py       # Provider configs
```

**Entry point:** `main.py` (FastAPI app initialization)

---

## 📦 Key Components

### API Routers

**Location:** `src/api/routers/`

**Purpose:** Define HTTP endpoints (routes).

**Key routers:**
- `tenders.py` - Tender CRUD endpoints
- `lots.py` - Lot CRUD endpoints
- `documents.py` - Document upload/download
- `ingestion.py` - RAG pipeline (parse, index, query)
- `ui.py` - Web UI routes (HTML templates)
- `milvus_route.py` - Milvus admin UI

**Example:**
```python
# src/api/routers/tenders.py
from fastapi import APIRouter, Depends
from src.schemas.tenders import TenderCreate, TenderRead
from src.services.tenders import TenderService

router = APIRouter(prefix="/api/tenders", tags=["tenders"])

@router.post("/", response_model=TenderRead)
async def create_tender(
    tender_data: TenderCreate,
    service: TenderService = Depends(get_tender_service)
):
    """Create new tender"""
    tender = await service.create_tender(**tender_data.dict())
    return tender
```

**Read more:** [API Endpoints](api-endpoints.md)

---

### Dependency Injection

**Location:** `src/api/deps.py`

**Purpose:** Provide dependencies to routes (services, database sessions).

**Key dependencies:**
- `get_session()` - Database session
- `get_tender_service()` - TenderService instance
- `get_lot_service()` - LotService instance
- `get_document_service()` - DocumentService instance
- `get_rag_pipeline()` - RAG pipeline

**Example:**
```python
# src/api/deps.py
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database import async_session
from src.services.tenders import TenderService

async def get_session() -> AsyncSession:
    """Get database session (closes automatically)"""
    async with async_session() as session:
        yield session

def get_tender_service(
    session: AsyncSession = Depends(get_session)
) -> TenderService:
    """Get TenderService with injected session"""
    return TenderService(session)
```

**Read more:** [Dependency Injection](dependency-injection.md)

---

### Request/Response Schemas

**Location:** `src/schemas/`

**Purpose:** Validate HTTP input/output with Pydantic.

**Schema patterns:**
- `*Create` - Request body for creation
- `*Update` - Request body for updates
- `*Read` - Response body (includes computed fields)
- `*List` - Paginated list response

**Example:**
```python
# src/schemas/tenders.py
from pydantic import BaseModel, Field
from datetime import date

class TenderCreate(BaseModel):
    """Request body for creating tender"""
    cig: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{10}$")
    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = None
    budget: float = Field(..., gt=0)
    deadline: date

class TenderRead(BaseModel):
    """Response body with tender data"""
    id: int
    cig: str
    title: str
    description: str | None
    budget: float
    deadline: date
    status: str
    created_at: datetime
    
    model_config = {"from_attributes": True}  # Load from ORM
```

---

## 🏗️ API Patterns

### Pattern 1: CRUD Endpoints

**Standard CRUD structure:**

```python
# src/api/routers/tenders.py
router = APIRouter(prefix="/api/tenders", tags=["tenders"])

@router.post("/", response_model=TenderRead, status_code=201)
async def create_tender(
    tender: TenderCreate,
    service: TenderService = Depends(get_tender_service)
):
    """Create tender"""
    return await service.create_tender(**tender.dict())

@router.get("/{tender_id}", response_model=TenderRead)
async def get_tender(
    tender_id: int,
    service: TenderService = Depends(get_tender_service)
):
    """Get tender by ID"""
    tender = await service.get_by_id(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return tender

@router.put("/{tender_id}", response_model=TenderRead)
async def update_tender(
    tender_id: int,
    tender_data: TenderUpdate,
    service: TenderService = Depends(get_tender_service)
):
    """Update tender"""
    return await service.update_tender(tender_id, **tender_data.dict(exclude_unset=True))

@router.delete("/{tender_id}", status_code=204)
async def delete_tender(
    tender_id: int,
    service: TenderService = Depends(get_tender_service)
):
    """Delete tender"""
    await service.delete_tender(tender_id)
```

---

### Pattern 2: List with Pagination

**Paginated list endpoints:**

```python
from src.schemas.common import PaginatedResponse

@router.get("/", response_model=PaginatedResponse[TenderRead])
async def list_tenders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: str | None = Query(None),
    service: TenderService = Depends(get_tender_service)
):
    """List tenders with pagination"""
    tenders = await service.list_tenders(skip=skip, limit=limit, status=status)
    total = await service.count_tenders(status=status)
    
    return {
        "items": tenders,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

---

### Pattern 3: File Upload

**Handle file uploads:**

```python
from fastapi import UploadFile, File

@router.post("/tenders/{tender_id}/documents")
async def upload_document(
    tender_id: int,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
):
    """Upload document for tender"""
    # Validate file type
    if not file.content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files supported")
    
    # Validate file size (max 50MB)
    if file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    
    document = await service.upload_document(file=file, tender_id=tender_id)
    return document
```

---

### Pattern 4: Error Handling

**Convert domain exceptions to HTTP errors:**

```python
@router.post("/tenders/{tender_id}/publish")
async def publish_tender(
    tender_id: int,
    service: TenderService = Depends(get_tender_service)
):
    """Publish tender"""
    try:
        tender = await service.publish_tender(tender_id)
        return tender
    except ValueError as e:
        # Domain validation error → 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected error → 500 Internal Server Error
        logger.error(f"Error publishing tender: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 🎯 Best Practices

### 1. Thin Controllers

**Routers should be thin (no business logic):**

```python
# ❌ Bad - business logic in router
@router.post("/tenders")
async def create_tender(tender: TenderCreate, session: AsyncSession = Depends(get_session)):
    # Validation in router (bad)
    if len(tender.cig) != 10:
        raise HTTPException(status_code=400, detail="Invalid CIG")
    
    # DB query in router (bad)
    existing = await session.execute(select(Tender).where(Tender.cig == tender.cig))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="CIG exists")
    
    # Create entity in router (bad)
    new_tender = Tender(**tender.dict())
    session.add(new_tender)
    await session.commit()
    return new_tender

# ✅ Good - delegate to service
@router.post("/tenders")
async def create_tender(
    tender: TenderCreate,
    service: TenderService = Depends(get_tender_service)
):
    try:
        return await service.create_tender(**tender.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

### 2. Use Response Models

**Always specify response models:**

```python
# ✅ Good - response model specified
@router.get("/tenders/{tender_id}", response_model=TenderRead)
async def get_tender(...):
    return tender  # Auto-serialized to TenderRead

# ❌ Bad - no response model (unsafe)
@router.get("/tenders/{tender_id}")
async def get_tender(...):
    return tender  # Might expose internal fields
```

---

### 3. Validate Query Parameters

**Use Query() for validation:**

```python
from fastapi import Query

@router.get("/tenders")
async def list_tenders(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    status: str | None = Query(None, regex="^(draft|published|archived)$")
):
    ...
```

---

### 4. Document Endpoints

**Use docstrings and OpenAPI metadata:**

```python
@router.post(
    "/tenders",
    response_model=TenderRead,
    status_code=201,
    summary="Create new tender",
    description="Create a new public procurement tender with validation",
    responses={
        201: {"description": "Tender created successfully"},
        400: {"description": "Invalid input data"},
        409: {"description": "CIG already exists"}
    }
)
async def create_tender(tender: TenderCreate, ...):
    """
    Create a new tender with the following validations:
    - CIG must be 10 digits
    - Budget must be positive
    - Deadline must be in the future
    """
    ...
```

---

## 🐛 Common Mistakes

### ❌ Business Logic in Routes

**Bad:**
```python
@router.post("/tenders/{tender_id}/publish")
async def publish_tender(tender_id: int, session: AsyncSession = Depends(get_session)):
    tender = await session.get(Tender, tender_id)
    if tender.status != "draft":  # ❌ Business rule in router
        raise HTTPException(400, "Can only publish drafts")
    tender.status = "published"
    await session.commit()
    return tender
```

**Good:**
```python
@router.post("/tenders/{tender_id}/publish")
async def publish_tender(
    tender_id: int,
    service: TenderService = Depends(get_tender_service)
):
    try:
        return await service.publish_tender(tender_id)  # ✅ Delegate
    except ValueError as e:
        raise HTTPException(400, str(e))
```

---

### ❌ Returning ORM Objects Directly

**Bad:**
```python
@router.get("/tenders/{tender_id}")
async def get_tender(tender_id: int, ...):
    tender = await service.get_by_id(tender_id)
    return tender  # ❌ Might expose password hashes, internal IDs
```

**Good:**
```python
@router.get("/tenders/{tender_id}", response_model=TenderRead)
async def get_tender(tender_id: int, ...):
    tender = await service.get_by_id(tender_id)
    return tender  # ✅ Serialized to TenderRead schema
```

---

## 📚 Related Documentation

- [Architecture Overview](../architecture/overview.md) - Layer dependencies
- [Domain Services](../domain/services.md) - Business logic layer
- [API Endpoints](api-endpoints.md) - Complete endpoint reference
- [Dependency Injection](dependency-injection.md) - DI patterns

---

**[⬆️ Documentation Home](../README.md) | [API Endpoints ➡️](api-endpoints.md)**

*Last updated: 2025-12-18*
