"""
Integration test fixtures
"""

from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.api.dependencies import get_db

# Use a separate test database for integration tests
INTEGRATION_DATABASE_URL = "sqlite+aiosqlite:///./test_integration.db"


@pytest.fixture(scope="function")
async def integration_db_engine():
    """Create a test database engine for integration tests."""
    engine = create_async_engine(
        INTEGRATION_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def integration_db_session(
    integration_db_engine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session for integration tests."""
    async_session_maker = sessionmaker(
        integration_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def integration_client(
    integration_db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client for integration tests.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield integration_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
