# Bot Class
import discord
from discord.ext import commands
import logging
import os

from core.config import Config

# Services
from services.mongo import MongoService
from services.redis import RedisService
from services.cache import CacheService
from services.rate_limiter import MemoryRateLimiter, RedisRateLimiter


class CyniBot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(
            command_prefix=Config.get_prefix,
            intents=intents,
            help_command=None
        )

        self.logger = logging.getLogger("cyni")

        # Services placeholders
        self.mongo = None
        self.redis = None
        self.cache = None
        self.rate_limiter = None

    # ---------------- SETUP ---------------- #

    async def setup_hook(self):
        await self.init_services()
        await self.load_modules()
        await self.tree.sync()

        self.logger.info("Bot setup complete")

    # ---------------- SERVICES ---------------- #

    async def init_services(self):
        # Mongo
        self.mongo = MongoService(os.getenv("MONGO_URI"))

        # Redis (optional)
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            self.redis = await RedisService.connect(redis_url)
            self.logger.info("Connected to Redis")
        else:
            self.redis = None
            self.logger.warning("Redis not found, using memory systems")

        # Cache
        self.cache = CacheService(self.mongo, self.redis)

        # Rate Limiter
        if self.redis:
            self.rate_limiter = RedisRateLimiter(self, self.redis)
        else:
            self.rate_limiter = MemoryRateLimiter(self)

    # ---------------- MODULES ---------------- #

    async def load_modules(self):
        # Auto-load modules
        for folder in ["modules", "events", "tasks"]:
            if not os.path.exists(folder):
                continue

            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith(".py") and not file.startswith("_"):
                        path = os.path.join(root, file)
                        module = path.replace("/", ".").replace("\\", ".")[:-3]

                        try:
                            await self.load_extension(module)
                            self.logger.info(f"Loaded {module}")
                        except Exception:
                            self.logger.exception(f"Failed to load {module}")

    # ---------------- GLOBAL CHECKS ---------------- #

    async def on_command(self, ctx):
        # Global rate limiter
        if ctx.guild:
            allowed, _ = await self.rate_limiter.consume(ctx.guild.id)

            if not allowed:
                raise commands.CommandOnCooldown(
                    commands.Cooldown(1, 5),
                    retry_after=5
                )

    # ---------------- EVENTS ---------------- #

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user} ({self.user.id})")

    # ---------------- SHUTDOWN ---------------- #

    async def close(self):
        self.logger.info("Shutting down...")

        if self.redis:
            await self.redis.close()

        if self.mongo:
            await self.mongo.close()

        await super().close()
        self.logger.info("Shutdown complete")