"""Endpoint s agregiranim statistikama (uz in-memory TTL caching)."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from tickethub import crud
from tickethub.cache import stats_cache
from tickethub.database import get_session
from tickethub.schemas import Stats

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stats"])

_CACHE_KEY = "stats"


@router.get("/stats", response_model=Stats)
async def get_stats(session: AsyncSession = Depends(get_session)) -> Stats:
    """Agregirane statistike ticketa. Rezultat se kratko kešira (TTL)."""
    cached = stats_cache.get(_CACHE_KEY)
    if cached is not None:
        logger.debug("Stats posluženo iz cachea.")
        return cached

    stats = Stats(**await crud.get_stats(session))
    stats_cache.set(_CACHE_KEY, stats)
    return stats
