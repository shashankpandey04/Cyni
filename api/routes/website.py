import os

import jwt
from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(
    prefix="/website",
    tags=["Website"],
)

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"


async def get_member(
    request: Request,
    guild_id: int,
):
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

    bot = request.app.state.bot

    guild = bot.get_guild(guild_id)
    if guild is None:
        raise HTTPException(
            status_code=404,
            detail="Guild not found.",
        )

    member = guild.get_member(payload["user_id"])
    if member is None:
        raise HTTPException(
            status_code=404,
            detail="Member not found.",
        )

    return guild, member


@router.get("/roles")
async def roles(
    guild_id: int = Query(...),
    request: Request = None,
):
    guild, member = await get_member(
        request,
        guild_id,
    )

    return {"roles": [role.id for role in member.roles if role != guild.default_role]}


@router.get("/access")
async def access(
    guild_id: int = Query(...),
    request: Request = None,
):
    bot = request.app.state.bot

    guild, member = await get_member(
        request,
        guild_id,
    )

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


@router.get("/me")
async def me(
    guild_id: int = Query(...),
    request: Request = None,
):
    bot = request.app.state.bot

    guild, member = await get_member(
        request,
        guild_id,
    )

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
        "access": {
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
        },
    }
