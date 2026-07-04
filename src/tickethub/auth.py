"""JWT autentifikacija: prijava preko DummyJSON-a, izdavanje i provjera tokena."""

from datetime import UTC, datetime, timedelta

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from tickethub.config import settings

bearer_scheme = HTTPBearer(auto_error=True)


async def authenticate_dummyjson(username: str, password: str) -> dict:
    """Provjeri kredencijale preko DummyJSON /auth/login. Vraća korisnika ili 401."""
    async with httpx.AsyncClient(
        base_url=settings.dummyjson_base_url, timeout=settings.http_timeout
    ) as client:
        resp = await client.post(
            "/auth/login", json={"username": username, "password": password}
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neispravno korisničko ime ili lozinka",
        )
    return resp.json()


def create_access_token(subject: str) -> str:
    """Izdaj vlastiti JWT (potpisan našim tajnim ključem)."""
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency: validira Bearer JWT i vraća payload (ili 401)."""
    try:
        return jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nevažeći ili istekao token",
        ) from exc
