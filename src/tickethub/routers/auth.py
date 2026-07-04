"""Autentifikacijski endpoint (prijava preko DummyJSON-a)."""

import logging

from fastapi import APIRouter

from tickethub.auth import authenticate_dummyjson, create_access_token
from tickethub.schemas import LoginRequest, TokenResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    """Provjeri kredencijale preko DummyJSON-a i izdaj vlastiti JWT."""
    user = await authenticate_dummyjson(payload.username, payload.password)
    token = create_access_token(subject=user.get("username", payload.username))
    logger.info("Uspješna prijava korisnika %s", payload.username)
    return TokenResponse(access_token=token)
