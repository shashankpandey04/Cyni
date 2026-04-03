#Mongo Connection + wrapper
import os
from pymongo import AsyncMongoClient


class MongoService:
    def __init__(self, uri: str):
        self.client = AsyncMongoClient(uri)
        self.db = self.client["cyni"]

    async def close(self):
        await self.client.close()

    # -------- GENERIC -------- #

    async def get(self, collection: str, _id):
        return await self.db[collection].find_one({"_id": _id})

    async def set(self, collection: str, _id, data: dict):
        await self.db[collection].update_one(
            {"_id": _id},
            {"$set": data},
            upsert=True
        )

    async def delete(self, collection: str, _id):
        await self.db[collection].delete_one({"_id": _id})

    # -------- ADVANCED -------- #

    async def insert(self, collection: str, data: dict):
        return await self.db[collection].insert_one(data)

    async def update(self, collection: str, query: dict, data: dict):
        return await self.db[collection].update_one(query, {"$set": data})

    async def find(self, collection: str, query: dict):
        cursor = self.db[collection].find(query)
        return [doc async for doc in cursor]