import os

import jwt
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

router = APIRouter(
    prefix="/website",
    tags=["Website"],
)

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"


class BulkAccessRequest(BaseModel):
    guild_ids: list[int]


async def get_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization")

    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing bearer token.",
        )

    token = auth[7:]

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid access token.",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type.",
        )

    return payload["user_id"]


async def get_member(
    bot,
    guild_id: int,
    user_id: int,
):
    guild = bot.get_guild(guild_id)

    if guild is None:
        return None, None

    member = guild.get_member(user_id)

    if member is None:
        return guild, None

    return guild, member


async def build_access(bot, guild, member):
    return {
        "administrator": member.guild_permissions.administrator,
        "discord": {
            "staff": await bot.staff_check(
                guild,
                member,
            ),
            "management": await bot.management_check(
                guild,
                member,
            ),
        },
        "roblox": {
            "staff": await bot.roblox_staff_check(
                guild,
                member,
            ),
            "management": await bot.roblox_management_check(
                guild,
                member,
            ),
        },
    }


@router.get("/roles")
async def roles(
    guild_id: int = Query(...),
    request: Request = None,
):
    bot = request.app.state.bot

    guild, member = await get_member(
        bot,
        guild_id,
        await get_user_id(request),
    )

    if guild is None:
        raise HTTPException(404, "Guild not found.")

    if member is None:
        raise HTTPException(404, "Member not found.")

    return {"roles": [role.id for role in member.roles if role != guild.default_role]}


@router.post("/access/bulk")
async def bulk_access(
    payload: BulkAccessRequest,
    request: Request,
):
    bot = request.app.state.bot

    user_id = await get_user_id(request)

    response = {}

    for guild_id in payload.guild_ids:
        guild, member = await get_member(
            bot,
            guild_id,
            user_id,
        )

        if guild is None or member is None:
            continue

        response[str(guild_id)] = await build_access(
            bot,
            guild,
            member,
        )

    return response


@router.get("/access")
async def access(
    guild_id: int = Query(...),
    request: Request = None,
):
    bot = request.app.state.bot

    guild, member = await get_member(
        bot,
        guild_id,
        await get_user_id(request),
    )

    if guild is None:
        raise HTTPException(404, "Guild not found.")

    if member is None:
        raise HTTPException(404, "Member not found.")

    return await build_access(
        bot,
        guild,
        member,
    )


@router.get("/me")
async def me(
    guild_id: int = Query(...),
    request: Request = None,
):
    bot = request.app.state.bot

    guild, member = await get_member(
        bot,
        guild_id,
        await get_user_id(request),
    )

    if guild is None:
        raise HTTPException(404, "Guild not found.")

    if member is None:
        raise HTTPException(404, "Member not found.")

    return {
        "user": {
            "id": member.id,
            "username": member.name,
            "display_name": member.display_name,
            "avatar": member.display_avatar.url,
        },
        "guild": {
            "id": guild.id,
            "name": guild.name,
            "icon": guild.icon.url if guild.icon else None,
        },
        "roles": [role.id for role in member.roles if role != guild.default_role],
        "access": await build_access(
            bot,
            guild,
            member,
        ),
    }
