import json
import asyncio
from typing import Any, Optional


class CacheService:

    DEFAULT_TTL = 300

    def __init__(self, mongo, redis=None):
        self.mongo = mongo
        self.redis = redis

        # Prevent duplicate DB fetches
        self._locks = {}

    # =========================================================
    # INTERNAL
    # =========================================================

    def _get_lock(self, key: str):
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        return self._locks[key]

    async def _get_redis_json(self, key: str):

        if not self.redis:
            return None

        try:
            data = await self.redis.get(key)

            if not data:
                return None

            return json.loads(data)

        except Exception:
            return None

    async def _set_redis_json(
        self,
        key: str,
        value: Any,
        ttl: int = DEFAULT_TTL
    ):

        if not self.redis:
            return

        try:
            await self.redis.set(
                key,
                json.dumps(value),
                ex=ttl
            )

        except Exception:
            pass

    async def delete(self, key: str):

        if not self.redis:
            return

        try:
            await self.redis.delete(key)
        except Exception:
            pass

    # =========================================================
    # SETTINGS
    # =========================================================

    async def get_settings(
        self,
        guild_id: int,
        *,
        force_fetch: bool = False
    ):

        key = f"guild:{guild_id}:settings"

        # ---------------- CACHE ---------------- #

        if not force_fetch:

            cached = await self._get_redis_json(key)

            if cached is not None:
                return cached

        # ---------------- LOCK ---------------- #

        async with self._get_lock(key):

            # double-check after lock

            if not force_fetch:

                cached = await self._get_redis_json(key)

                if cached is not None:
                    return cached

            # ---------------- DATABASE ---------------- #

            data = await self.mongo.get(
                "settings",
                guild_id
            ) or {}

            # ---------------- CACHE ---------------- #

            await self._set_redis_json(
                key,
                data,
                ttl=300
            )

            return data

    async def invalidate_settings(self, guild_id: int):

        await self.delete(
            f"guild:{guild_id}:settings"
        )

    # =========================================================
    # PREMIUM
    # =========================================================

    async def is_premium(
        self,
        guild_id: int
    ) -> bool:

        key = f"guild:{guild_id}:premium"

        # ---------------- CACHE ---------------- #

        if self.redis:

            try:
                cached = await self.redis.get(key)

                if cached is not None:
                    return cached == "1"

            except Exception:
                pass

        # ---------------- DATABASE ---------------- #

        data = await self.mongo.get(
            "premium",
            guild_id
        )

        premium = data is not None

        # ---------------- CACHE ---------------- #

        if self.redis:

            try:
                await self.redis.set(
                    key,
                    "1" if premium else "0",
                    ex=300
                )

            except Exception:
                pass

        return premium

    async def invalidate_premium(self, guild_id: int):

        await self.delete(
            f"guild:{guild_id}:premium"
        )

    # =========================================================
    # AUDIT LOG CHANNEL
    # =========================================================

    async def get_audit_log_channel(
        self,
        guild_id: int
    ) -> Optional[int]:

        key = f"guild:{guild_id}:auditlog"

        # ---------------- CACHE ---------------- #

        if self.redis:

            try:
                cached = await self.redis.get(key)

                if cached:
                    return int(cached)

            except Exception:
                pass

        # ---------------- SETTINGS ---------------- #

        settings = await self.get_settings(guild_id)

        moderation = settings.get(
            "moderation_module",
            {}
        )

        if not moderation.get("enabled"):
            return None

        channel_id = moderation.get("audit_log")

        if not channel_id:
            return None

        # ---------------- CACHE ---------------- #

        if self.redis:

            try:
                await self.redis.set(
                    key,
                    str(channel_id),
                    ex=600
                )

            except Exception:
                pass

        return channel_id

    async def recover_audit_log_channel(
        self,
        guild_id: int
    ):

        key = f"guild:{guild_id}:auditlog"

        # remove stale cache
        await self.delete(key)

        # refetch fresh
        return await self.get_audit_log_channel(
            guild_id
        )