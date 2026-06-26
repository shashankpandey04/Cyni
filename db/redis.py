import os

from redis.asyncio import Redis


class MemoryRedis:
    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value, ex=None):
        self._store[key] = value

    async def delete(self, key):
        self._store.pop(key, None)

    async def exists(self, key):
        return key in self._store

    async def ping(self):
        return True

    async def aclose(self):
        pass


REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    redis = Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )
else:
    redis = MemoryRedis()
