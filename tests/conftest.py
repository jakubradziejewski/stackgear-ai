"""
tests/conftest.py

Shared fixtures for all tests.
Creates a fresh in-memory SQLite database for each test function —
completely isolated from the live Neon database.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User
from app.models.hardware import Hardware
from app.models.enums import HardwareStatus


# ---------------------------------------------------------------------------
# In-memory SQLite engine — created once per test, thrown away after
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ---------------------------------------------------------------------------
# HTTP client wired to the test database
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(db_session):
    """AsyncClient that uses the in-memory DB instead of Neon."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Seed fixtures — users
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def admin_user(db_session):
    user = User(
        id="admin-001",
        email="admin@test.com",
        username="admin",
        password_hash=hash_password("admin123"),
        is_admin=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def regular_user(db_session):
    user = User(
        id="user-001",
        email="user@test.com",
        username="user",
        password_hash=hash_password("user123"),
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user


# ---------------------------------------------------------------------------
# Seed fixtures — hardware
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def available_item(db_session):
    item = Hardware(
        id="hw-available",
        name="Test Laptop",
        brand="Dell",
        status=HardwareStatus.AVAILABLE,
    )
    db_session.add(item)
    await db_session.commit()
    return item


@pytest_asyncio.fixture
async def repair_item(db_session):
    item = Hardware(
        id="hw-repair",
        name="Broken Mouse",
        brand="Razer",
        status=HardwareStatus.REPAIR,
    )
    db_session.add(item)
    await db_session.commit()
    return item


@pytest_asyncio.fixture
async def in_use_item(db_session, regular_user):
    item = Hardware(
        id="hw-in-use",
        name="Rented Phone",
        brand="Apple",
        status=HardwareStatus.IN_USE,
        rented_by_id=regular_user.id,
    )
    db_session.add(item)
    await db_session.commit()
    return item


# ---------------------------------------------------------------------------
# Auth helper — returns a Bearer token for a given user
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def admin_token(client, admin_user):
    response = await client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "admin123",
    })
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def user_token(client, regular_user):
    response = await client.post("/auth/login", json={
        "email": "user@test.com",
        "password": "user123",
    })
    return response.json()["access_token"]