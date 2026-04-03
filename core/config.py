# Env + Config Loader
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # -------- ENV -------- #

    MONGO_URI = os.getenv("MONGO_URI")
    REDIS_URL = os.getenv("REDIS_URL")

    PRODUCTION_TOKEN = os.getenv("PRODUCTION_TOKEN")
    PREMIUM_TOKEN = os.getenv("PREMIUM_TOKEN")
    DEV_TOKEN = os.getenv("DEV_TOKEN")

    DEFAULT_PREFIX = "!"

    # -------- TOKEN -------- #

    @classmethod
    def get_token(cls):
        return (
            cls.PRODUCTION_TOKEN
            or cls.PREMIUM_TOKEN
            or cls.DEV_TOKEN
        )

    # -------- PREFIX -------- #

    @staticmethod
    async def get_prefix(bot, message):
        if not message.guild:
            return Config.DEFAULT_PREFIX

        try:
            settings = await bot.cache.get_settings(message.guild.id)
            return settings.get("prefix", Config.DEFAULT_PREFIX)
        except Exception:
            return Config.DEFAULT_PREFIX