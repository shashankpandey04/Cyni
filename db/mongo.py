import os

from pymongo import AsyncMongoClient

MONGO_URI = os.getenv("MONGO_URI")

client = AsyncMongoClient(MONGO_URI)
db = client["cyni"]
