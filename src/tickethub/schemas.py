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

class TicketCreate(BaseModel):
    """Ulaz za POST /tickets."""

    model_config = ConfigDict(use_enum_values=True)

    title: str = Field(min_length=1, max_length=255)
    status: Status = Status.open
    priority: Priority = Priority.medium
    assignee: str | None = None


class TicketUpdate(BaseModel):
    """Ulaz za PATCH /tickets/{id} (sva polja opcionalna)."""

    model_config = ConfigDict(use_enum_values=True)

    status: Status | None = None
    priority: Priority | None = None
    assignee: str | None = None

class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class Stats(BaseModel):
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]

class SyncResult(BaseModel):
    synced: int
