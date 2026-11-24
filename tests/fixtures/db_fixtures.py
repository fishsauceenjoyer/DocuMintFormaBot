"""Database fixtures for integration tests.

Provides an in-memory SQLite database with all tables created, so
CRUD operations can be tested without touching the real database file.
"""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture
async def mock_db_session():
    """Create an in-memory SQLite async session for integration tests.

    Creates all tables before yield and drops them after the test.
    """
    from db.models import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    TestSession = async_sessionmaker(engine, expire_on_commit=False)
    async with TestSession() as db:
        try:
            yield db
        finally:
            await db.close()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
