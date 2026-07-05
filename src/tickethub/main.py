"""FastAPI aplikacija: lifespan (startup sync + background job), logiranje,
rate limiting i registracija routera."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from tickethub.config import settings
from tickethub.database import SessionLocal
from tickethub.routers import admin, auth, stats, tickets
from tickethub.services.sync import periodic_sync, sync_if_empty

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("tickethub")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.sync_on_startup:
        async with SessionLocal() as session:
            await sync_if_empty(session)

    # Pozadinski sync job (uključen samo ako je interval > 0).
    task: asyncio.Task | None = None
    if settings.sync_interval_seconds > 0:
        task = asyncio.create_task(
            periodic_sync(SessionLocal, settings.sync_interval_seconds)
        )

    yield

    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])

app = FastAPI(
    title="TicketHub",
    version="0.1.0",
    description="Middleware REST servis koji prikuplja, pohranjuje i izlaže support tickete.",
    lifespan=lifespan,
)

# Rate limiting (globalno preko middlewarea).
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logira svaki zahtjev (metoda, put, status, trajanje)."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    level = logging.WARNING if response.status_code >= 400 else logging.INFO
    logger.log(
        level,
        "%s %s -> %d (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


app.include_router(tickets.router)
app.include_router(auth.router)
app.include_router(stats.router)
app.include_router(admin.router)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
