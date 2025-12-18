# 🗄️ Infrastructure: Database

> **SQLAlchemy database infrastructure with async session management**

This module provides database connectivity and ORM base classes for all domain entities.

---

## 📍 Location

**Directory:** `src/infra/database/`

**Files:**
- `base.py` - SQLAlchemy declarative base
- `session.py` - Async session factory and connection pool
- `__init__.py` - Public exports

---

## 🔌 Components

### Database Base

**Location:** `src/infra/database/base.py`

SQLAlchemy declarative base for all ORM models.

```python
from src.infra.database import Base

class MyModel(Base):
    __tablename__ = "my_table"
    # SQLAlchemy automatically generates __tablename__ from class name
    # MyModel → "mymodel"
```

**Features:**
- ✅ Auto-generates `__tablename__` from class name (lowercase)
- ✅ Shared base for all entities across the application
- ✅ Type-safe with proper annotations

---

### Database Session

**Location:** `src/infra/database/session.py`

Async session management with connection pooling.

```python
from src.infra.database import get_db, async_session, engine

# Usage 1: Dependency injection (FastAPI)
from fastapi import Depends

@app.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()

# Usage 2: Context manager (services)
async with async_session() as session:
    result = await session.execute(select(Item))
    items = result.scalars().all()
    
# Usage 3: Direct engine access (migrations, testing)
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

**Configuration:**

From `configs/config.py`:
```python
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"
```

Engine settings:
- `echo=False` - Disable SQL logging (set to True for debugging)
- `statement_cache_size=0` - Disable prepared statement cache
- `prepared_statement_cache_size=0` - Prevent caching issues with asyncpg

---

## 🎯 Usage in Domain Layer

### Define Entity

```python
# src/domain/tender/entities/tender.py
from uuid import uuid4
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from src.infra.database import Base

class Tender(Base):
    __tablename__ = "tenders"  # Optional: auto-generated if omitted
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String, nullable=False)
    cig = Column(String, unique=True, nullable=False)
```

### Create Service

```python
# src/domain/tender/services/tender.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tender.entities import Tender

class TenderService:
    @staticmethod
    async def get_by_id(db: AsyncSession, tender_id: UUID) -> Tender | None:
        result = await db.execute(
            select(Tender).where(Tender.id == tender_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, data: TenderCreate) -> Tender:
        tender = Tender(**data.model_dump())
        db.add(tender)
        await db.commit()
        await db.refresh(tender)
        return tender
```

### Use in API

```python
# src/api/routers/tenders.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_db
from src.domain.tender.services import TenderService

router = APIRouter()

@router.get("/tenders/{tender_id}")
async def get_tender(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    tender = await TenderService.get_by_id(db, tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")
    return tender
```

---

## 🔄 Migration from Old Structure

**Before (Wrong):**
```python
# ❌ Root level db/ (not in src/)
from src.infra.database import Base
from src.infra.database import get_db
```

**After (Correct):**
```python
# ✅ src/infra/database/ (infrastructure layer)
from src.infra.database import Base, get_db
```

**Why?**
- Database is **infrastructure concern** (not core business logic)
- Should be in `src/infra/` per Clean Architecture
- Easy to swap databases (PostgreSQL → MySQL → SQLite) without touching domain

---

## 🧪 Testing

### Create Test Database

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool

from src.infra.database import Base

@pytest.fixture
async def test_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=NullPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(test_db):
    async with AsyncSession(test_db) as session:
        yield session
```

### Test Service

```python
async def test_create_tender(db_session):
    data = TenderCreate(title="Test Tender", cig="12345")
    tender = await TenderService.create(db_session, data)
    
    assert tender.id is not None
    assert tender.title == "Test Tender"
```

---

## 🔧 Advanced Configuration

### Connection Pool Tuning

```python
# src/infra/database/session.py
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,              # Max connections in pool
    max_overflow=20,           # Extra connections beyond pool_size
    pool_timeout=30,           # Timeout waiting for connection
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Verify connections before using
)
```

### Multiple Databases

```python
# src/infra/database/session.py
primary_engine = create_async_engine(settings.PRIMARY_DB_URL)
analytics_engine = create_async_engine(settings.ANALYTICS_DB_URL)

primary_session = async_sessionmaker(primary_engine)
analytics_session = async_sessionmaker(analytics_engine)

async def get_primary_db():
    async with primary_session() as session:
        yield session

async def get_analytics_db():
    async with analytics_session() as session:
        yield session
```

---

## 📚 See Also

- [Domain Entities](../domain/entities.md) - Using Base in domain models
- [Alembic Migrations](../guides/migrations.md) - Database schema changes
- [Storage Infrastructure](storage.md) - File storage (Supabase)
- [Architecture Overview](../architecture/overview.md) - Clean Architecture principles
