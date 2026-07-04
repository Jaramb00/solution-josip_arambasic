"""Read endpointi za tickete."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from tickethub import crud
from tickethub.auth import require_auth
from tickethub.database import get_session
from tickethub.models import Ticket
from tickethub.schemas import (
    PaginatedTickets,
    Priority,
    Status,
    TicketCreate,
    TicketDetail,
    TicketListItem,
    TicketUpdate,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _to_list_item(ticket: Ticket) -> TicketListItem:
    """Mapira ORM Ticket u listnu stavku (opis skraćen na 100 znakova)."""
    return TicketListItem(
        id=ticket.id,
        title=ticket.title,
        status=ticket.status,
        priority=ticket.priority,
        description=ticket.title[:100],
    )


@router.get("", response_model=PaginatedTickets)
async def list_tickets(
    status: Status | None = None,
    priority: Priority | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> PaginatedTickets:
    """Paginirana lista ticketa uz opcionalno filtriranje po statusu/prioritetu."""
    total, rows = await crud.list_tickets(
        session,
        status=status.value if status else None,
        priority=priority.value if priority else None,
        limit=limit,
        offset=offset,
    )
    return PaginatedTickets(
        total=total, limit=limit, offset=offset, items=[_to_list_item(t) for t in rows]
    )


@router.get("/search", response_model=PaginatedTickets)
async def search_tickets(
    q: str = Query(min_length=1, description="Pojam za pretragu po nazivu"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> PaginatedTickets:
    """Pretraga ticketa po nazivu (case-insensitive, djelomično podudaranje)."""
    total, rows = await crud.search_tickets(session, q=q, limit=limit, offset=offset)
    return PaginatedTickets(
        total=total, limit=limit, offset=offset, items=[_to_list_item(t) for t in rows]
    )


@router.get("/{ticket_id}", response_model=TicketDetail)
async def get_ticket(
    ticket_id: int, session: AsyncSession = Depends(get_session)
) -> Ticket:
    """Detalji ticketa uključujući puni JSON iz izvora."""
    ticket = await crud.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Ticket nije pronađen"
        )
    return ticket

@router.post(
    "",
    response_model=TicketDetail,
    status_code=http_status.HTTP_201_CREATED,
    dependencies=[Depends(require_auth)],
)
async def create_ticket(
    payload: TicketCreate, session: AsyncSession = Depends(get_session)
) -> Ticket:
    """Kreira novi ticket (id dodjeljuje baza)."""
    return await crud.create_ticket(session, payload.model_dump())


@router.patch(
    "/{ticket_id}",
    response_model=TicketDetail,
    dependencies=[Depends(require_auth)],
)
async def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    session: AsyncSession = Depends(get_session),
) -> Ticket:
    """Izmjena ticketa (status/priority/assignee); promjena preživljava restart."""
    ticket = await crud.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Ticket nije pronađen"
        )
    changes = payload.model_dump(exclude_unset=True)
    if changes:
        ticket = await crud.update_ticket(session, ticket, changes)
    return ticket
