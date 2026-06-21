from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings



DATABASE_URL = str(settings.DATABASE_URL)


engine: AsyncEngine = create_async_engine(DATABASE_URL, future=True, echo=False)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
