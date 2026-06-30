import asyncio
import os

import uvicorn
from discord.ext import commands

from api.server import create_app


class API(commands.Cog):
    """Internal FastAPI server."""

    def __init__(self, bot):
        self.bot = bot
        self.app = create_app(bot)

    async def cog_load(self):
        config = uvicorn.Config(
            app=self.app,
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", 5000)),
            log_level="warning",
        )

        self.server = uvicorn.Server(config)
        self.task = asyncio.create_task(self.server.serve())

    async def cog_unload(self):
        self.server.should_exit = True
        await self.task


async def setup(bot):
    await bot.add_cog(API(bot))
