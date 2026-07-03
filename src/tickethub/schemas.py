"""Pydantic modeli (ulaz/izlaz) i enumeracije."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Status(str, Enum):
    open = "open"
    closed = "closed"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TicketListItem(BaseModel):
    """Stavka u paginiranoj listi (opis skraćen na <= 100 znakova)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: Status
    priority: Priority
    description: str = Field(max_length=100)


class TicketDetail(BaseModel):
    """Detalji ticketa + puni JSON iz izvora."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: Status
    priority: Priority
    assignee: str | None = None
    source: dict[str, Any] | None = None


class PaginatedTickets(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TicketListItem]
