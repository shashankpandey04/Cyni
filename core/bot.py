import logging
import os

import discord
import httpx
from discord.ext import commands

from core.config import Config
from db.mongo import client as mongo_client
from db.mongo import db
from db.redis import redis
from integrations.erlc.client import ERLC


class CyniBot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(
            command_prefix=Config.get_prefix,
            intents=intents,
            help_command=None,
        )

        self.logger = logging.getLogger("cyni")

        self.http_client = httpx.AsyncClient(timeout=15)

        # Database
        self.mongo = mongo_client
        self.db = db
        self.redis = redis

        self.erlc = ERLC(self.http_client)

    # ---------------- SETUP ---------------- #

    async def setup_hook(self):
        await self.mongo.admin.command("ping")

        if self.redis:
            await self.redis.ping()

        await self.load_modules()

        await self.tree.sync()

        self.logger.info("Bot setup complete")

    # ---------------- MODULES ---------------- #

    async def load_modules(self):
        for folder in ("modules", "events", "tasks"):
            if not os.path.isdir(folder):
                continue

            for root, _, files in os.walk(folder):
                for file in files:
                    if not file.endswith(".py") or file.startswith("_"):
                        continue

                    module = os.path.splitext(os.path.join(root, file))[0].replace(
                        os.sep, "."
                    )

                    try:
                        await self.load_extension(module)
                        self.logger.info(f"Loaded {module}")
                    except Exception:
                        self.logger.exception(f"Failed to load {module}")

    # ---------------- EVENTS ---------------- #

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user}")

    # ---------------- SHUTDOWN ---------------- #

    async def close(self):
        self.logger.info("Shutting down...")

        await self.mongo.close()

        if self.redis:
            await self.redis.aclose()

        await self.http_client.aclose()

        await super().close()

        self.logger.info("Shutdown complete")
