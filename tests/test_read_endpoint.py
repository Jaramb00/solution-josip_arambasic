"""Integracijski testovi read endpointa."""


async def test_list_tickets_paginated(client, seeded):
    resp = await client.get("/tickets?limit=2&offset=0")
    body = resp.json()

    assert resp.status_code == 200
    assert body["total"] == 3
    assert [t["id"] for t in body["items"]] == [1, 2]
    assert "source" not in body["items"][0]          # lista ne curi puni JSON


async def test_list_tickets_filtering(client, seeded):
    resp = await client.get("/tickets?status=closed&priority=high")
    body = resp.json()

    assert body["total"] == 1
    assert body["items"][0]["id"] == 2


async def test_search_by_title(client, seeded):
    resp = await client.get("/tickets/search?q=POEM")   # case-insensitive

    assert [t["id"] for t in resp.json()["items"]] == [2]


async def test_get_ticket_detail_includes_source(client, seeded):
    resp = await client.get("/tickets/2")
    body = resp.json()

    assert resp.status_code == 200
    assert body["assignee"] == "bob"
    assert body["source"] == {"id": 2, "todo": "Memorize a poem"}


async def test_get_missing_ticket_404(client, seeded):
    assert (await client.get("/tickets/999")).status_code == 404


async def test_invalid_status_422(client, seeded):
    assert (await client.get("/tickets?status=banana")).status_code == 422
