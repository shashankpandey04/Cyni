from motor.motor_asyncio import AsyncIOMotorClient
from DataBase.database import Database

import os
import dotenv
import logging

dotenv.load_dotenv()

class MongoDBHandler(Database):
    def __init__(self):
        self.db = None

    async def connect(self):
        MONGO_URI = os.getenv('MONGO_URI')
        if not MONGO_URI:
            raise ValueError("MongoDB URI is not provided")

        ENV = os.getenv('ENV', 'DEVELOPMENT')
        DB = 'cyni' if ENV == 'PRODUCTION' else 'cyni-dev'

        try:
            client = AsyncIOMotorClient(MONGO_URI)
            self.db = client[DB]
            logging.info(f"Connected to MongoDB ({DB})")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def save_settings(self, settings: dict):
        """
        Save the settings to the MongoDB database.
        :param settings (dict): The settings to save.
        
        """
        try:
            await self.db.settings.update_one(
                {"guild_id": settings['guild_id']},
                {"$set": settings},
                upsert=True
            )
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            raise