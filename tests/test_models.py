"""Roundtrip test za Ticket model (upis i čitanje iz baze)."""

from sqlalchemy import select

from tickethub.models import Ticket


async def test_ticket_roundtrip(session_factory):
    async with session_factory() as session:
        session.add(Ticket(id=1, title="Test", status="open", priority="low",
                           assignee="alice", source={"id": 1, "todo": "Test"}))
        await session.commit()

    async with session_factory() as session:
        ticket = (await session.execute(select(Ticket))).scalar_one()

    assert ticket.title == "Test"
    assert ticket.source == {"id": 1, "todo": "Test"}
    assert ticket.created_at is not None
