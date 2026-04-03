# Redis Client
import redis.asyncio as redis


class RedisService:
    def __init__(self, client):
        self.client = client

    @classmethod
    async def connect(cls, url: str):
        client = redis.from_url(url, decode_responses=True)
        return cls(client)

    async def get(self, key: str):
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: int = None):
        await self.client.set(key, value, ex=ex)

    async def delete(self, key: str):
        await self.client.delete(key)

    async def close(self):
        await self.client.close()