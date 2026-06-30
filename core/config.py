# Env + Config Loader
import os

from dotenv import load_dotenv

from db.mongo import db

load_dotenv()


class Config:
    # -------- ENV -------- #

    MONGO_URI = os.getenv("MONGO_URI")
    REDIS_URL = os.getenv("REDIS_URL")

    PRODUCTION_TOKEN = os.getenv("PRODUCTION_TOKEN")
    DEV_TOKEN = os.getenv("DEV_TOKEN")

    DEFAULT_PREFIX = "?"

    # -------- TOKEN -------- #

    @classmethod
    def get_token(cls) -> str:
        token = cls.PRODUCTION_TOKEN or cls.DEV_TOKEN

        if token is None:
            raise RuntimeError("No Discord token found in enviornment variable.")

        return token

    # -------- PREFIX -------- #

    @staticmethod
    async def get_prefix(bot, message):
        if not message.guild:
            return Config.DEFAULT_PREFIX

        settings = await db.settings.find_one(
            {"_id": message.guild.id},
            {"prefix": 1},
        )

        if settings:
            return settings.get("prefix", Config.DEFAULT_PREFIX)

        return Config.DEFAULT_PREFIX
