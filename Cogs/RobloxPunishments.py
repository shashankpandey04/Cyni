import discord
from discord.ext import commands
import time

import roblox

from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR
from discord import app_commands
from cyni import is_management, is_staff, premium_check
from utils.utils import log_command_usage
import re
from utils.pagination import Pagination

class RobloxPunishments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="punishments",
        aliases=["punish", "p"],
    )
    @commands.guild_only()
    async def punishment(self, ctx):
        """
        Manage Roblox punishments commands.
        """
        pass

    @punishment.command(
        name="log",
        aliases=["v"],
    )
    @commands.guild_only()
    async def view(self, ctx, roblox: str = None, user: discord.User = None):
        """
        View Roblox punishments for a user.
        """
        pass

    @punishment.command(
        name="view",
        aliases=["v"],
    )
    @commands.guild_only()
    async def view_punishments(self, ctx, roblox: str = None, user: discord.User = None):
        """View a user's Roblox punishments."""
        if not roblox and not user:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You must provide either a Roblox username or a Discord user.",
                    color=RED_COLOR
                )
            )
        pass

    @punishment.command(
        name="manage",
        aliases=["m"],
    )
    @commands.guild_only()
    async def manage(self, ctx, punishment_id: int = None):
        """
        Manage Roblox punishments.
        """
        pass


async def setup(bot):
    await bot.add_cog(RobloxPunishments(bot))