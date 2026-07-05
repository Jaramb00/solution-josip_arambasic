"""Testovi za /sync endpoint i periodic_sync job."""

import asyncio

from tickethub.services import sync as sync_module


async def test_sync_requires_auth(client, seeded):
    assert (await client.post("/sync")).status_code == 403


async def test_sync_endpoint_upserts(client, seeded, auth_headers, monkeypatch):
    async def fake_fetch():
        return [{"id": 1, "title": "Refreshed", "status": "open",
                 "priority": "low", "assignee": None, "source": {"id": 1}}]
    monkeypatch.setattr(sync_module, "fetch_tickets", fake_fetch)

    resp = await client.post("/sync", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json() == {"synced": 1}
    detail = await client.get("/tickets/1")
    assert detail.json()["title"] == "Refreshed"


async def test_periodic_sync_runs_and_cancels(session_factory, monkeypatch):
    calls = 0

    async def fake_fetch():
        nonlocal calls
        calls += 1
        return []
    monkeypatch.setattr(sync_module, "fetch_tickets", fake_fetch)

    task = asyncio.create_task(sync_module.periodic_sync(session_factory, 0))
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert calls >= 1
    assert task.cancelled() or task.done()
