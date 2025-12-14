from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from configs.config import settings
from typing import AsyncGenerator

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
