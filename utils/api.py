#Cyni API

import discord

from discord.ext import commands


class API(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(API(bot))
