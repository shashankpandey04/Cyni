import asyncio
import json
from typing import Any, TypeVar

from pydantic import BaseModel

from models.settings.settings import GuildSettings

T = TypeVar("T", bound=BaseModel)


class CacheService:
    DEFAULT_TTL = 300

    def __init__(self, mongo, redis=None):
        self.mongo = mongo
        self.redis = redis

        self._locks: dict[str, asyncio.Lock] = {}

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

    async def _set_redis_json(self, key: str, value: Any, ttl: int = DEFAULT_TTL):

        if not self.redis:
            return

        try:
            await self.redis.set(key, json.dumps(value), ex=ttl)

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
    # GENERIC MODEL CACHE
    # =========================================================

    async def get_model(
        self, collection: str, _id: int, model: type[T], *, force_fetch: bool = False
    ) -> T:

        key = f"{collection}:{_id}"

        # ---------------- CACHE ---------------- #

        if not force_fetch:
            cached = await self._get_redis_json(key)

            if cached is not None:
                return model.model_validate(cached)

        # ---------------- LOCK ---------------- #

        async with self._get_lock(key):
            if not force_fetch:
                cached = await self._get_redis_json(key)

                if cached is not None:
                    return model.model_validate(cached)

            # ---------------- DATABASE ---------------- #

            data = await self.mongo.get(collection, _id)

            if not data:
                data = {"_id": _id}

            # ---------------- CACHE ---------------- #

            await self._set_redis_json(key, data, ttl=self.DEFAULT_TTL)

            return model.model_validate(data)

    async def save_model(self, collection: str, model_instance: BaseModel):

        doc = model_instance.model_dump(by_alias=True)

        _id = doc["_id"]

        await self.mongo.set(
            collection, _id, {k: v for k, v in doc.items() if k != "_id"}
        )

        await self._set_redis_json(f"{collection}:{_id}", doc, ttl=self.DEFAULT_TTL)

    async def invalidate_model(self, collection: str, _id: int):

        await self.delete(f"{collection}:{_id}")

    # =========================================================
    # SETTINGS
    # =========================================================

    async def get_settings(
        self, guild_id: int, *, force_fetch: bool = False
    ) -> GuildSettings:

        return await self.get_model(
            "settings", guild_id, GuildSettings, force_fetch=force_fetch
        )

    async def save_settings(self, settings: GuildSettings):

        await self.save_model("settings", settings)

    async def invalidate_settings(self, guild_id: int):

        await self.invalidate_model("settings", guild_id)

    # =========================================================
    # PREMIUM
    # =========================================================

    async def is_premium(self, guild_id: int) -> bool:

        key = f"premium:{guild_id}"

        if self.redis:
            try:
                cached = await self.redis.get(key)

                if cached is not None:
                    return cached == "1"

            except Exception:
                pass

        data = await self.mongo.get("premium", guild_id)

        premium = data is not None

        if self.redis:
            try:
                await self.redis.set(key, "1" if premium else "0", ex=self.DEFAULT_TTL)

            except Exception:
                pass

        return premium

    async def invalidate_premium(self, guild_id: int):

        await self.delete(f"premium:{guild_id}")

    # =========================================================
    # HELPERS
    # =========================================================

    async def get_audit_log_channel(self, guild_id: int):

        key = f"auditlog:{guild_id}"

        if self.redis:
            try:
                cached = await self.redis.get(key)

                if cached:
                    return int(cached)

            except Exception:
                pass

        settings = await self.get_settings(guild_id)

        if not settings.moderation.enabled:
            return None

        channel_id = settings.moderation.audit_log

        if not channel_id:
            return None

        if self.redis:
            try:
                await self.redis.set(key, str(channel_id), ex=600)

            except Exception:
                pass

        return channel_id

    async def recover_audit_log_channel(self, guild_id: int):

        await self.delete(f"auditlog:{guild_id}")

        return await self.get_audit_log_channel(guild_id)
