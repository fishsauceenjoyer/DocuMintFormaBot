"""Database fixtures for integration tests.

Provides an in-memory SQLite database with all tables created, so
CRUD operations can be tested without touching the real database file.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def mock_db_session():
    """Create an in-memory SQLite session for integration tests.

    Creates all tables before yield and drops them after the test.
    """
    from db.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    db = TestSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)