import json
import os

import httpx

from db.mongo import db
from db.redis import redis

from .exceptions import ERLCAPIError, get_error_message
from .models import Server


class ERLC:
    BASE_URL = os.getenv("PRC_API_URL", "https://api.erlc.gg/v2")

    def __init__(self, http_client: httpx.AsyncClient):
        self.client = http_client

    def _check_api_error(self, data: dict):
        """Raises ERLCAPIError if the API returned an error code."""

        if not isinstance(data, dict):
            return

        code = data.get("code")

        if code is None:
            return

        if code in (
            0,
            1001,
            1002,
            2000,
            2001,
            2002,
            2003,
            2004,
            3001,
            3002,
            4000,
            4001,
            4002,
            4003,
            9998,
            9999,
        ):
            raise ERLCAPIError(
                code,
                get_error_message(code),
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
            raise ERLCAPIError(
                2000,
                "No ERLC API key has been configured for this Discord server.",
            )

        api_key = document["key"]

        await redis.set(cache_key, api_key, ex=3600)

        return api_key

    async def request(self, guild_id: int, endpoint: str) -> dict:
        cache_key = f"erlc:{guild_id}:{endpoint.lstrip('/')}"

        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        api_key = await self._get_api_key(guild_id)

        try:
            response = await self.client.get(
                f"{self.BASE_URL}{endpoint}",
                headers={
                    "server-key": api_key,
                },
            )

            data = response.json()

            self._check_api_error(data)

            if response.status_code >= 400:
                raise ERLCAPIError(
                    response.status_code,
                    f"HTTP {response.status_code}",
                )

        except httpx.TimeoutException:
            raise ERLCAPIError(
                1001,
                "Request to the ERLC API timed out.",
            )

        except httpx.RequestError:
            raise ERLCAPIError(
                1001,
                "Failed to communicate with the ERLC API.",
            )

        await redis.set(
            cache_key,
            json.dumps(data),
            ex=20,
        )

        return data

    async def post(
        self,
        guild_id: int,
        endpoint: str,
        payload: dict,
    ) -> dict:
        api_key = await self._get_api_key(guild_id)

        try:
            response = await self.client.post(
                f"{self.BASE_URL}{endpoint}",
                json=payload,
                headers={
                    "server-key": api_key,
                },
            )

            data = response.json()

            self._check_api_error(data)

            if response.status_code >= 400:
                raise ERLCAPIError(
                    response.status_code,
                    f"HTTP {response.status_code}",
                )

            return data

        except httpx.TimeoutException:
            raise ERLCAPIError(
                1001,
                "Request to the ERLC API timed out.",
            )

        except httpx.RequestError:
            raise ERLCAPIError(
                1001,
                "Failed to communicate with the ERLC API.",
            )

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
