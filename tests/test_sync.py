"""Testovi sync logike (fetch_tickets je mockan — bez mreže)."""

from sqlalchemy import select

from tickethub.models import Ticket
from tickethub.services import sync as sync_module


def _fake_rows(title="From source"):
    return [{"id": 1, "title": title, "status": "open", "priority": "medium",
             "assignee": "alice", "source": {"id": 1}}]


async def test_sync_inserts_new_rows(session_factory, monkeypatch):
    async def fake_fetch():
        return _fake_rows()
    monkeypatch.setattr(sync_module, "fetch_tickets", fake_fetch)

    async with session_factory() as session:
        count = await sync_module.sync_tickets(session)

    assert count == 1
    async with session_factory() as session:
        ticket = (await session.execute(select(Ticket))).scalar_one()
    assert ticket.title == "From source"


async def test_sync_updates_existing_rows(session_factory, monkeypatch):
    async def fake_fetch():
        return _fake_rows(title="Updated title")
    monkeypatch.setattr(sync_module, "fetch_tickets", fake_fetch)

    async with session_factory() as session:
        session.add(Ticket(id=1, title="Old", status="closed", priority="low"))
        await session.commit()

    async with session_factory() as session:
        await sync_module.sync_tickets(session)
        ticket = (await session.execute(select(Ticket))).scalar_one()

    assert ticket.title == "Updated title"   # osvježeno iz izvora
    assert ticket.status == "open"


async def test_sync_if_empty_skips_populated_db(session_factory, monkeypatch):
    called = False

    async def fake_fetch():
        nonlocal called
        called = True
        return _fake_rows()
    monkeypatch.setattr(sync_module, "fetch_tickets", fake_fetch)

    async with session_factory() as session:
        session.add(Ticket(id=99, title="Existing", status="open", priority="low"))
        await session.commit()

    async with session_factory() as session:
        count = await sync_module.sync_if_empty(session)

    assert count == 0
    assert called is False   # nije ni pokušao dohvatiti izvor
