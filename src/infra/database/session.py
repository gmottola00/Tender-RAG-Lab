"""Database session management and connection pool."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from configs.config import settings

# Create async engine with connection pool
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)

# Session factory for creating async sessions
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator for database sessions.
    
    Yields an AsyncSession that is automatically closed when done.
    Use with FastAPI's Depends() for dependency injection.
    
    Usage:
        >>> from fastapi import Depends
        >>> from sqlalchemy.ext.asyncio import AsyncSession
        >>> from src.infra.database import get_db
        >>> 
        >>> @router.get("/items")
        >>> async def list_items(db: AsyncSession = Depends(get_db)):
        ...     result = await db.execute(select(Item))
        ...     return result.scalars().all()
    
    Yields:
        AsyncSession: Database session instance
    """
    async with async_session() as session:
        yield session
