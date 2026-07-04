"""Testovi /stats endpointa i cache ponašanja."""

import pytest

from tickethub.cache import stats_cache


@pytest.fixture(autouse=True)
def _clean_cache():
    """Cache je globalan (modul-level) pa ga čistimo oko svakog testa."""
    stats_cache.clear()
    yield
    stats_cache.clear()


async def test_stats_aggregates(client, seeded):
    resp = await client.get("/stats")
    body = resp.json()

    assert resp.status_code == 200
    assert body["total"] == 3
    assert body["by_status"] == {"open": 1, "closed": 2}
    assert body["by_priority"] == {"low": 1, "medium": 1, "high": 1}


async def test_stats_served_from_cache(client, seeded):
    first = (await client.get("/stats")).json()
    # Promijenimo bazu "iza leđa" cachea (direktno, bez API-ja koji bi ga clearao)
    async with seeded() as session:
        from tickethub.models import Ticket
        session.add(Ticket(id=50, title="Sneaky", status="open", priority="low"))
        await session.commit()

    second = (await client.get("/stats")).json()
    assert second == first                     # i dalje stara vrijednost -> cache radi


async def test_write_invalidates_cache(client, seeded, auth_headers):
    before = (await client.get("/stats")).json()
    await client.post("/tickets", json={"title": "New"}, headers=auth_headers)

    after = (await client.get("/stats")).json()
    assert after["total"] == before["total"] + 1   # clear() na write
