"""Pytest fixtures: izolirana test-baza (SQLite u temp datoteci)."""

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tickethub.database import Base, get_session
from tickethub.main import app
from tickethub.models import Ticket

SAMPLE_TICKETS = [
    {"id": 1, "title": "Do the dishes", "status": "open", "priority": "medium",
     "assignee": "alice", "source": {"id": 1, "todo": "Do the dishes"}},
    {"id": 2, "title": "Memorize a poem", "status": "closed", "priority": "high",
     "assignee": "bob", "source": {"id": 2, "todo": "Memorize a poem"}},
    {"id": 3, "title": "Watch a classic movie", "status": "closed", "priority": "low",
     "assignee": "carol", "source": {"id": 3, "todo": "Watch a classic movie"}},
]

@pytest_asyncio.fixture
async def session_factory(tmp_path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    url = f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}"
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()

@pytest_asyncio.fixture
async def seeded(session_factory):
    async with session_factory() as session:
        session.add_all(Ticket(**row) for row in SAMPLE_TICKETS)
        await session.commit()
    return session_factory


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
