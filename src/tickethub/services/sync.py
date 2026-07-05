"""Seed/sync logika: puni lokalnu bazu iz vanjskog izvora (DummyJSON)."""

import asyncio
import logging

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tickethub.models import Ticket
from tickethub.services.dummyjson import fetch_tickets

logger = logging.getLogger(__name__)

_UPDATABLE = ("title", "status", "priority", "assignee", "source")


def _upsert_stmt(dialect_name: str, rows: list[dict]):
    """Sastavi INSERT ... ON CONFLICT DO UPDATE za SQLite ili PostgreSQL."""
    insert = {"sqlite": sqlite_insert, "postgresql": pg_insert}[dialect_name]
    stmt = insert(Ticket).values(rows)
    return stmt.on_conflict_do_update(
        index_elements=[Ticket.id],
        set_={col: getattr(stmt.excluded, col) for col in _UPDATABLE},
    )


async def count_tickets(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(Ticket))
    return int(result.scalar_one())


async def sync_tickets(session: AsyncSession) -> int:
    """Dohvati tickete iz izvora i upsertaj ih u bazu. Vraća broj zapisa.

    Upsert (umjesto brisanja pa ponovnog inserta) čuva lokalno kreirane
    tickete, a polja postojećih osvježava iz izvora.
    """
    rows = await fetch_tickets()
    if not rows:
        logger.warning("Vanjski izvor nije vratio nijedan ticket.")
        return 0

    dialect = session.get_bind().dialect.name
    await session.execute(_upsert_stmt(dialect, rows))
    await session.commit()
    logger.info("Sinkronizirano %d ticketa iz vanjskog izvora.", len(rows))
    return len(rows)


async def sync_if_empty(session: AsyncSession) -> int:
    """Napuni bazu samo ako je prazna (koristi se na startupu)."""
    if await count_tickets(session) > 0:
        logger.info("Baza već sadrži tickete, preskačem startup sync.")
        return 0
    return await sync_tickets(session)

async def periodic_sync(
    session_factory: async_sessionmaker[AsyncSession], interval_seconds: int
) -> None:
    """Pozadinski job koji periodički osvježava podatke iz izvora.

    Pokreće se kao asyncio task; prekida se (CancelledError) na gašenju app-a.
    """
    logger.info("Pozadinski sync pokrenut (svakih %d s).", interval_seconds)
    try:
        while True:
            await asyncio.sleep(interval_seconds)
            try:
                async with session_factory() as session:
                    await sync_tickets(session)
            except Exception:
                logger.exception("Pozadinski sync nije uspio; pokušavam ponovno kasnije.")
    except asyncio.CancelledError:
        logger.info("Pozadinski sync zaustavljen.")
        raise
