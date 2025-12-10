from app.db.session import get_db  # ora è async
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    async for db in get_db():
        yield db
