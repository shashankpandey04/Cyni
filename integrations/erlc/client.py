import json
import os

import httpx

from db.mongo import db
from db.redis import redis

from .models import Server


class ERLC:
    BASE_URL = os.getenv("PRC_API_URL", "https://api.erlc.gg/v2")

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=15,
        )

    async def _get_api_key(self, guild_id: int) -> str:
        cache_key = f"erlc:key:{guild_id}"

        api_key = await redis.get(cache_key)
        if api_key:
            return api_key

        document = await db.erlc.find_one(
            {"_id": guild_id},
            {"key": 1},
        )

        if document is None:
            raise ValueError("ERLC API key is not configured for this guild.")

        api_key = document["key"]

        await redis.set(cache_key, api_key, ex=3600)

        return api_key

    async def request(self, guild_id: int, endpoint: str) -> dict:
        cache_key = f"erlc:{guild_id}:{endpoint.lstrip('/')}"

        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        api_key = await self._get_api_key(guild_id)

        response = await self.client.get(
            endpoint,
            headers={
                "server-key": api_key,
            },
        )

        response.raise_for_status()

        data = response.json()

        await redis.set(
            cache_key,
            json.dumps(data),
            ex=10,
        )

        return data

    async def post(self, guild_id: int, endpoint: str, payload: dict) -> dict:
        api_key = await self._get_api_key(guild_id)

        response = await self.client.post(
            endpoint,
            json=payload,
            headers={
                "server-key": api_key,
            },
        )

        response.raise_for_status()

        return response.json()

    async def server(self, guild_id: int) -> Server:
        data = await self.request(guild_id, "/server")
        return Server.model_validate(data)

    async def command(self, guild_id: int, command: str) -> dict:
        return await self.post(
            guild_id,
            "/server/command",
            {
                "command": command,
            },
        )

    async def hint(self, guild_id: int, message: str) -> dict:
        return await self.command(
            guild_id,
            f":h {message}",
        )

    async def message(self, guild_id: int, message: str) -> dict:
        return await self.command(
            guild_id,
            f":m {message}",
        )

    async def private_message(
        self,
        guild_id: int,
        username: str,
        message: str,
    ) -> dict:
        return await self.command(
            guild_id,
            f":pm {username} {message}",
        )

    async def close(self):
        await self.client.aclose()
