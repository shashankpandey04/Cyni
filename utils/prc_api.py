import discord
import asyncio
import roblox
import datetime
from discord.ext import commands
import json
from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
from bson import ObjectId
import aiohttp
import typing


class ServerLinkNotFound(commands.CheckFailure):
    pass

class ResponseFailed(Exception):
    detail: str | None
    code: int | None
    data: str

    def __init__(self, data: str, detail: str | None = None, code: int | None = None, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self) -> str:
        return f"ResponseFailed(data={self.data}, detail={self.detail}, code={self.code})"

class ServerStatus():
    Name: str | None = None
    OwnerId: int | None = None
    CoOwnerIds: list[int] | None = None
    CurrentPlayers: int | None = None
    MaxPlayers: int | None = None
    JoinKey: str | None = None
    AccVerifiedReq: str = ""
    TeamBalance: bool = False

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
class ServerPlayers():
    Player: str | None
    Permission: str
    Callsign: str | None
    Team: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerJoinLogs():
    Join: bool
    Timestamp: int
    Player: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerQueue():
    total_players: int

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerKillLogs():
    killed: str | None
    timestamp: int
    killer: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerCommandLogs():
    player: str | None
    timestamp: int
    command: str | None


class ServerModCalls():
    caller: str | None
    moderator: str | None
    timestamp: int

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerBans():
    player_id: int

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerVehicles():
    texture: str | None
    name: str | None
    owner: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerCommand():
    command: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class PRC_API_Client:
    def __init__(self,bot,base_url: str, api_key: str):
        self.bot = bot
        self.base_url = base_url
        self.api_key = api_key
        self.session = aiohttp.ClientSession()

    async def close(self):
        await self.session.close()


    async def fetch_server_key(self, server_id: int):
        return await self.bot.erlc_keys.find_by_id(server_id)

    async def _send_test_request(self,key: str):
        async with self.session.get(f"{self.base_url}/server", headers={"Server-Key": key}) as resp:
            data = await resp.json()
            if resp.status == 200:
                return True
            else:
                raise ResponseFailed(data, detail=data.get("detail"), code=data.get("code"))
            
    async def _fetch_server_status(self, server_id: int):
        server_key = await self.fetch_server_key(server_id)
        if not server_key:
            raise ServerLinkNotFound("Server link not found")
        async with self.session.get(f"{self.base_url}/server", headers={"Server-Key": server_key["key"]}) as resp:
            data = await resp.json()
            if resp.status == 200:
                return ServerStatus(**data)
            elif resp.status == 429:
                retry_after = data.get("retry_after")
                await asyncio.sleep(retry_after)
                return await self._fetch_server_status(server_id)
            else:
                raise ResponseFailed(data, detail=data.get("detail"), code=data.get("code"))
            
    async def _fetch_server_players(self, server_id: int):
        server_key = await self.fetch_server_key(server_id)
        if not server_key:
            raise ServerLinkNotFound("Server link not found")
        async with self.session.get(f"{self.base_url}/server/players", headers={"Server-Key": server_key["key"]}) as resp:
            data = await resp.json()
            if resp.status == 200:
                return [ServerPlayers(**x) for x in data]
            elif resp.status == 429:
                retry_after = data.get("retry_after")
                await asyncio.sleep(retry_after)
                return await self._fetch_server_players(server_id)
            else:
                raise ResponseFailed(data, detail=data.get("detail"), code=data.get("code"))
            
    async def _fetch_server_join_logs(self, server_id: int):
        server_key = await self.fetch_server_key(server_id)
        if not server_key:
            raise ServerLinkNotFound("Server link not found")
        async with self.session.get(f"{self.base_url}/server/joinlogs", headers={"Server-Key": server_key["key"]}) as resp:
            data = await resp.json()
            if resp.status == 200:
                return [ServerJoinLogs(**x) for x in data]
            elif resp.status == 429:
                retry_after = data.get("retry_after")
                await asyncio.sleep(retry_after)
                return await self._fetch_server_join_logs(server_id)
            else:
                raise ResponseFailed(data, detail=data.get("detail"), code=data.get("code"))