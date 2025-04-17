from src.config import db_settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

async_engine = create_async_engine(
    url=db_settings.database_url_asyncpg(),
    echo=True,
    pool_size=5,
)

async_session = async_sessionmaker(async_engine, expire_on_commit=False)

async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        yield session