import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_startup_saas.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-local-pytest")
os.environ.setdefault("ENABLE_BACKGROUND_JOBS", "false")

from app import models  # noqa: F401, E402
from app.api import deps  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402


def engine_options(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"poolclass": NullPool}


database_url = os.environ["DATABASE_URL"]
engine = create_async_engine(database_url, **engine_options(database_url))
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def reset_database() -> AsyncGenerator[None, None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[deps.get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    def build(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    return build


async def register_user(
    client: AsyncClient,
    *,
    email: str = "owner@example.com",
    password: str = "strong-password",
    full_name: str = "Example User",
) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def create_workspace(
    client: AsyncClient,
    token: str,
    *,
    name: str = "Acme Operations",
) -> dict:
    response = await client.post(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def create_project(
    client: AsyncClient,
    token: str,
    workspace_id: str,
    *,
    name: str = "Growth Launch",
) -> dict:
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name, "description": "Coordinate launch tasks."},
    )
    assert response.status_code == 201, response.text
    return response.json()
