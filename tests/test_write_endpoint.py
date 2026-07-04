"""Integracijski testovi write endpointa (POST, PATCH)."""


async def test_create_ticket(client, seeded, auth_headers):
    resp = await client.post(
        "/tickets",
        json={"title": "New ticket", "priority": "high"},
        headers=auth_headers,
    )
    body = resp.json()

    assert resp.status_code == 201
    assert body["id"] == 4                      # baza dodijelila sljedeći id
    assert body["status"] == "open"             # default
    assert body["priority"] == "high"

    detail = await client.get(f"/tickets/{body['id']}")
    assert detail.status_code == 200            # stvarno je u bazi


async def test_create_ticket_validation(client, seeded, auth_headers):
    resp = await client.post("/tickets", json={"title": ""}, headers=auth_headers)
    assert resp.status_code == 422


async def test_patch_updates_only_sent_fields(client, seeded, auth_headers):
    resp = await client.patch(
        "/tickets/1", json={"status": "closed"}, headers=auth_headers
    )
    body = resp.json()

    assert resp.status_code == 200
    assert body["status"] == "closed"
    assert body["assignee"] == "alice"          # NIJE pregažen None-om


async def test_patch_missing_ticket_404(client, seeded, auth_headers):
    resp = await client.patch(
        "/tickets/999", json={"status": "open"}, headers=auth_headers
    )
    assert resp.status_code == 404


async def test_patch_invalid_priority_422(client, seeded, auth_headers):
    resp = await client.patch(
        "/tickets/1", json={"priority": "urgent"}, headers=auth_headers
    )
    assert resp.status_code == 422
