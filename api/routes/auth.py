import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRY = 60 * 15  # 15 minutes
REFRESH_TOKEN_EXPIRY = 60 * 60 * 24 * 30  # 30 days


class TokenRequest(BaseModel):
    guild_id: int
    user_id: int


@router.post("/token")
async def issue_tokens(
    payload: TokenRequest,
    request: Request,
):
    bot = request.app.state.bot

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        raise HTTPException(404, "Guild not found.")

    member = guild.get_member(payload.user_id)
    if member is None:
        raise HTTPException(404, "Member not found.")

    now = datetime.now(timezone.utc)

    access_token = jwt.encode(
        {
            "guild_id": guild.id,
            "user_id": member.id,
            "type": "access",
            "exp": now + timedelta(seconds=ACCESS_TOKEN_EXPIRY),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    session_id = secrets.token_urlsafe(32)

    refresh_token = jwt.encode(
        {
            "guild_id": guild.id,
            "user_id": member.id,
            "type": "refresh",
            "jti": session_id,
            "exp": now + timedelta(seconds=REFRESH_TOKEN_EXPIRY),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    await bot.redis.set(
        f"refresh:{session_id}",
        f"{guild.id}:{member.id}",
        ex=REFRESH_TOKEN_EXPIRY,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRY,
    }


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
async def refresh_access_token(
    payload: RefreshRequest,
    request: Request,
):
    bot = request.app.state.bot

    try:
        data = jwt.decode(
            payload.refresh_token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid refresh token.")

    if data.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type.")

    session = await bot.redis.get(f"refresh:{data['jti']}")

    if session is None:
        raise HTTPException(401, "Session expired.")

    access_token = jwt.encode(
        {
            "guild_id": data["guild_id"],
            "user_id": data["user_id"],
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_EXPIRY),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    return {
        "access_token": access_token,
        "expires_in": ACCESS_TOKEN_EXPIRY,
    }


@router.post("/logout")
async def logout(
    payload: RefreshRequest,
    request: Request,
):
    bot = request.app.state.bot

    try:
        data = jwt.decode(
            payload.refresh_token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid refresh token.")

    await bot.redis.delete(f"refresh:{data['jti']}")

    return {
        "success": True,
    }


@router.get("/verify")
async def verify(
    request: Request,
):
    auth = request.headers.get("Authorization")

    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token.")

    token = auth[7:]

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid access token.")

    if payload.get("type") != "access":
        raise HTTPException(401, "Invalid token type.")

    return {
        "valid": True,
        "guild_id": payload["guild_id"],
        "user_id": payload["user_id"],
    }
