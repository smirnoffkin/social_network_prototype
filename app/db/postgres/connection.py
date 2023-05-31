from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy_utils import create_database, database_exists

from app.config import settings

Base = declarative_base()

engine = create_async_engine(
    url=settings.async_database_url,
    pool_pre_ping=True,
    echo=True,
    future=True
)
async_session = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)


if not database_exists(url=settings.database_url):
    create_database(url=settings.database_url)


async def get_db() -> AsyncGenerator:
    session: AsyncSession = async_session()
    try:
        yield session
    finally:
        await session.close()
