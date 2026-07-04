"""Testovi JWT zaštite i login endpointa."""

from tickethub import auth as auth_module


async def test_write_without_token_rejected(client, seeded):
    resp = await client.post("/tickets", json={"title": "X"})
    assert resp.status_code == 403          # HTTPBearer: nema Authorization headera


async def test_write_with_invalid_token_401(client, seeded):
    resp = await client.post("/tickets", json={"title": "X"},
                             headers={"Authorization": "Bearer nije-jwt"})
    assert resp.status_code == 401


async def test_login_issues_usable_token(client, seeded, monkeypatch):
    async def fake_authenticate(username, password):
        return {"username": username}
    monkeypatch.setattr(auth_module, "authenticate_dummyjson", fake_authenticate)
    # patchamo i referencu koju drži router (from-import!)
    from tickethub.routers import auth as auth_router
    monkeypatch.setattr(auth_router, "authenticate_dummyjson", fake_authenticate)

    login = await client.post("/auth/login",
                              json={"username": "emilys", "password": "x"})
    token = login.json()["access_token"]

    resp = await client.post("/tickets", json={"title": "Via token"},
                             headers={"Authorization": f"Bearer {token}"})
    assert login.status_code == 200
    assert resp.status_code == 201
