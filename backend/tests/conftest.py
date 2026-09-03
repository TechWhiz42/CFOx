import os

# Configure test-only environment BEFORE importing app modules.
# This keeps tests independent of a developer's local .env file.
os.environ.setdefault(
    "AUTH_SECRET_KEY",
    "test-secret-key-for-cfox",
)
os.environ.setdefault(
    "DATABASE_URL",
    "sqlite:///./test_runtime.db",
)
os.environ.setdefault(
    "RAZORPAY_WEBHOOK_SECRET",
    "test-webhook-secret",
)
os.environ.setdefault(
    "RAZORPAY_WEBHOOK_USER_ID",
    "1",
)

import pytest

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(
        bind=engine
    )

    Session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    session = Session()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db):
    """Unauthenticated test client."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as client:
        yield client

    app.dependency_overrides.clear()
