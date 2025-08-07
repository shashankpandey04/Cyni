import discord
from discord.ext import commands
import time

from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR
from discord import app_commands
from cyni import is_management, is_staff, premium_check
from utils.utils import log_command_usage
import re
from utils.pagination import Pagination

class ShiftManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="shift",
        aliases=["shifts"],
    )
    @commands.guild_only()
    async def shift(self, ctx):
        """
        Manage shifts commands.
        """
        pass

    @shift.command(
        name="manage",
        aliases=["m"],
    )
    @commands.guild_only()
    async def manage(self, ctx, type: str = None):
        """
        Manage shifts.
        """
        pass

    @shift.command(
        name="view",
        aliases=["v"],
    )
    @commands.guild_only()
    async def view(self, ctx, type: str = None):
        """
        View shifts.
        """
        pass

    @shift.command(
        name="active",
        aliases=["a"],
    )
    @commands.guild_only()
    async def active(self, ctx, type: str = None):
        """
        View active shifts.
        """
        pass

    @shift.command(
        name="history",
        aliases=["h"],
    )
    @commands.guild_only()
    async def history(self, ctx, type: str = None):
        """
        View shift history.
        """
        pass

async def setup(bot):
    await bot.add_cog(ShiftManager(bot))