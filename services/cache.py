# Cache Layer (Permissions, Prefix)
import json


class CacheService:
    def __init__(self, mongo, redis=None):
        self.mongo = mongo
        self.redis = redis

    # -------- SETTINGS -------- #

    async def get_settings(self, guild_id):
        key = f"guild:{guild_id}:settings"

        if self.redis:
            cached = await self.redis.get(key)
            if cached:
                return json.loads(cached)

        data = await self.mongo.get("settings", guild_id) or {}

        if self.redis:
            await self.redis.set(key, json.dumps(data), ex=60)

        return data

    async def invalidate_settings(self, guild_id):
        if self.redis:
            await self.redis.delete(f"guild:{guild_id}:settings")

    # -------- PREMIUM -------- #

    async def is_premium(self, guild_id):
        key = f"guild:{guild_id}:premium"

        if self.redis:
            cached = await self.redis.get(key)
            if cached:
                return cached == "1"

        data = await self.mongo.get("premium", guild_id)
        is_premium = data is not None

        if self.redis:
            await self.redis.set(key, "1" if is_premium else "0", ex=60)

        return is_premium