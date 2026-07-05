"""Administrativni endpointi (ručno okidanje sinkronizacije). Zaštićeno JWT-om."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from tickethub.auth import require_auth
from tickethub.cache import stats_cache
from tickethub.database import get_session
from tickethub.schemas import SyncResult
from tickethub.services.sync import sync_tickets

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


@router.post("/sync", response_model=SyncResult, dependencies=[Depends(require_auth)])
async def trigger_sync(session: AsyncSession = Depends(get_session)) -> SyncResult:
    """Ručno osvježi tickete iz vanjskog izvora (upsert u lokalnu bazu)."""
    count = await sync_tickets(session)
    stats_cache.clear()  # podaci su se možda promijenili
    return SyncResult(synced=count)
