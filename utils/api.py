from fastapi import FastAPI, APIRouter, Depends, Header, HTTPException
from typing import Optional
from pydantic import BaseModel
from discord.ext import commands
import discord
import os
from dotenv import load_dotenv
import motor.motor_asyncio
import redis.asyncio as redis
import json

from cyni import management_check, staff_check, roblox_staff_check

# ========================
# 🔧 Setup
# ========================

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN", "dev_token")
MONGO_URI = os.getenv("MONGO_URI")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

mongo = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = mongo["cyni"]

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="CYNI Bot API", version="3.1")
router = APIRouter(prefix="/api")

async def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or authorization != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

class GuildsRequest(BaseModel):
    user_id: int
    refresh: Optional[bool] = False

class AccessRequest(BaseModel):
    user_id: int

def serialize_guild(guild: discord.Guild):
    return {
        "id": str(guild.id),
        "name": guild.name,
        "icon": guild.icon.url if guild.icon else None,
    }

async def compute_permission_level(bot, guild, member):
    if await management_check(bot, guild, member):
        return 1
    elif await staff_check(bot, guild, member):
        return 2
    elif await roblox_staff_check(bot, guild, member):
        return 3
    return 0

async def track_user_guild(user_id: int, guild_id: str):
    await redis_client.sadd(f"user_guilds:{guild_id}", user_id)

class APIRoutes:

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        router.add_api_route("/guilds", self.get_guilds, methods=["POST"], dependencies=[Depends(verify_token)])
        router.add_api_route("/guilds/{guild_id}/access", self.check_access, methods=["POST"], dependencies=[Depends(verify_token)])

    async def get_guilds(self, body: GuildsRequest):
        user_id = body.user_id
        cache_key = f"guilds:{user_id}"

        if not body.refresh:
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

        results = []

        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if not member:
                continue

            permission_level = await compute_permission_level(self.bot, guild, member)

            if permission_level == 0:
                continue

            await track_user_guild(user_id, str(guild.id))

            results.append({
                **serialize_guild(guild),
                "hasBot": True,
                "permission_level": permission_level
            })

        await redis_client.set(cache_key, json.dumps(results), ex=60)

        return results

    # ========================
    # POST /guilds/{guild_id}/access
    # ========================
    async def check_access(self, guild_id: str, body: AccessRequest):
        user_id = body.user_id

        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")

        member = guild.get_member(user_id)
        if not member:
            raise HTTPException(status_code=404, detail="User not in guild")

        permission_level = await compute_permission_level(self.bot, guild, member)

        return {
            "permission_level": permission_level
        }

class ServerAPI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        APIRoutes(self.bot)
        app.include_router(router)

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerAPI(bot))