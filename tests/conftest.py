import asyncio
from unittest import mock

import pytest
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists

from app.main import app
from app.config import settings
from app.db.postgres.connection import get_db
from app.db.postgres.models import Base
from app.services.oauth2 import create_access_token

DATABASE_URL = f"{settings.database_url}_test"
ASYNC_DATABASE_URL = f"{settings.async_database_url}_test"

sync_engine = create_engine(url=DATABASE_URL, pool_pre_ping=True)
async_engine = create_async_engine(
    url=ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    echo=True,
    future=True
)
testing_async_session = sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
async def prepare_database():
    if not database_exists(DATABASE_URL):
        create_database(DATABASE_URL)

    Base.metadata.drop_all(bind=sync_engine)
    Base.metadata.create_all(bind=sync_engine)


@pytest.fixture
async def session():
    db: AsyncSession = testing_async_session()
    try:
        yield db
    finally:
        await db.close()


@pytest.fixture
async def client(session):
    async def override_get_db():
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    # https://github.com/long2ice/fastapi-cache/issues/49
    # https://github.com/encode/httpx/issues/350
    mock.patch("fastapi_cache.decorator.cache", lambda *args, **kwargs: lambda f: f).start()
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client


async def create_test_auth_headers_for_user(email: str) -> dict:
    access_token = await create_access_token(data={"sub": email})
    return {"Authorization": f"Bearer {access_token}"}
