import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from src.main import app
from src.engine.database import get_session

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async def override_get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="module", autouse=True)
def _clear_dependency_override_after_module():
    # app.dependency_overrides is a global, shared across every test module in
    # the session. Without this, the override set above at import time leaks
    # into every test file collected after this one, silently redirecting
    # their DB-backed dependencies to this file's throwaway in-memory engine.
    yield
    app.dependency_overrides.pop(get_session, None)

@pytest.fixture(autouse=True)
def setup_db():
    async def init():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
    asyncio.run(init())
    yield
    async def teardown():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
    asyncio.run(teardown())

client = TestClient(app)

def test_register_user():
    response = client.post("/auth/register", json={"username": "testuser", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User created successfully"
    assert "user_id" in data

def test_register_user_duplicate():
    client.post("/auth/register", json={"username": "duplicate_user", "password": "password123"})
    response = client.post("/auth/register", json={"username": "duplicate_user", "password": "password123"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

def test_login_success():
    client.post("/auth/register", json={"username": "loginuser", "password": "securepassword"})
    # /auth/token is an OAuth2PasswordRequestForm endpoint: it expects form-encoded data, not JSON.
    response = client.post("/auth/token", data={"username": "loginuser", "password": "securepassword"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure():
    client.post("/auth/register", json={"username": "baduser", "password": "password"})
    response = client.post("/auth/token", data={"username": "baduser", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
