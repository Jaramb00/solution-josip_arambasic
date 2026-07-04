"""FastAPI aplikacija: lifespan (startup sync) i health check."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from tickethub.config import settings
from tickethub.database import SessionLocal
from tickethub.routers import auth, tickets
from tickethub.services.sync import sync_if_empty

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("tickethub")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.sync_on_startup:
        async with SessionLocal() as session:
            await sync_if_empty(session)
    yield


app = FastAPI(
    title="TicketHub",
    version="0.1.0",
    description="Middleware REST servis koji prikuplja, pohranjuje i izlaže support tickete.",
    lifespan=lifespan,
)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(tickets.router)
app.include_router(auth.router)
