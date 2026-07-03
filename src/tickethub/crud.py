"""Sloj za pristup podacima (upiti nad bazom) — odvojen od HTTP sloja."""

from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tickethub.models import Ticket


def _apply_filters(
    stmt: Select, status: str | None = None, priority: str | None = None
) -> Select:
    if status is not None:
        stmt = stmt.where(Ticket.status == status)
    if priority is not None:
        stmt = stmt.where(Ticket.priority == priority)
    return stmt


async def _count(session: AsyncSession, stmt: Select) -> int:
    """Prebroji retke koje bi dani SELECT vratio (bez limita/offseta)."""
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    return int((await session.execute(count_stmt)).scalar_one())


async def list_tickets(
    session: AsyncSession,
    *,
    status: str | None = None,
    priority: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[int, Sequence[Ticket]]:
    """Paginirana i filtrirana lista ticketa. Vraća (ukupno, retci)."""
    stmt = _apply_filters(select(Ticket), status, priority)
    total = await _count(session, stmt)
    stmt = stmt.order_by(Ticket.id).limit(limit).offset(offset)
    rows = (await session.execute(stmt)).scalars().all()
    return total, rows


async def search_tickets(
    session: AsyncSession, *, q: str, limit: int = 20, offset: int = 0
) -> tuple[int, Sequence[Ticket]]:
    """Pretraga po nazivu (case-insensitive). Vraća (ukupno, retci)."""
    stmt = select(Ticket).where(Ticket.title.ilike(f"%{q}%"))
    total = await _count(session, stmt)
    stmt = stmt.order_by(Ticket.id).limit(limit).offset(offset)
    rows = (await session.execute(stmt)).scalars().all()
    return total, rows


async def get_ticket(session: AsyncSession, ticket_id: int) -> Ticket | None:
    return await session.get(Ticket, ticket_id)
