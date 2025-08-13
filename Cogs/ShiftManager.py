import discord
from discord.ext import commands
import time

from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR
from discord import app_commands
from cyni import is_roblox_management, is_roblox_staff
from utils.utils import log_command_usage
from utils.autocompletes import shift_type_autocomplete
from utils.pagination import Pagination
from Views.ShiftManager import *

    # shift_types = data["shift_types"]

    # if shift_types and len(shift_types) != 0:
    #     return [
    #         app_commands.Choice(
    #             name=shift_type.get("shift_name", "Unknown"),
    #             value=shift_type.get("shift_name", "Unknown")
    #         )
    #         for shift_type in shift_types
    #     ]
    # else:
    #     return [
    #         app_commands.Choice(
    #             name="Default",
    #             value="default"
    #         ),
    #     ]




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
    @is_roblox_staff()
    @app_commands.autocomplete(type=shift_type_autocomplete)
    async def manage(self, ctx, type: str):
        """
        Manage shifts.
        """
        shift_types = await self.bot.shift_types.find_by_id(ctx.guild.id)
        filtered_shift_types = list(shift_types.keys()) if isinstance(shift_types, dict) else ["default"]
        if type not in filtered_shift_types:
            return await ctx.send(
                embed=discord.Embed(
                    title="Invalid Shift Type",
                    description="Please make sure you have selected a valid shift type.",
                    color=RED_COLOR
                )
            )

    @shift.command(
        name="view",
        aliases=["v"],
    )
    @commands.guild_only()
    @is_roblox_staff()
    @app_commands.autocomplete(type=shift_type_autocomplete)
    async def view(self, ctx, type: str):
        """
        View shifts.
        """
        shift_types = await self.bot.shift_types.find_by_id(ctx.guild.id)
        filtered_shift_types = list(shift_types.keys()) if isinstance(shift_types, dict) else ["default"]
        if type not in filtered_shift_types:
            return await ctx.send(
                embed=discord.Embed(
                    title="Invalid Shift Type",
                    description="Please make sure you have selected a valid shift type.",
                    color=RED_COLOR
                )
            )

    @shift.command(
        name="active",
        aliases=["a"],
    )
    @commands.guild_only()
    @is_roblox_staff()
    @app_commands.autocomplete(type=shift_type_autocomplete)
    async def active(self, ctx, type: str):
        """
        View active shifts.
        """
        shift_types = await self.bot.shift_types.find_by_id(ctx.guild.id)
        filtered_shift_types = list(shift_types.keys()) if isinstance(shift_types, dict) else ["default"]
        if type not in filtered_shift_types:
            return await ctx.send(
                embed=discord.Embed(
                    title="Invalid Shift Type",
                    description="Please make sure you have selected a valid shift type.",
                    color=RED_COLOR
                )
            )


    @shift.command(
        name="history",
        aliases=["h"],
    )
    @commands.guild_only()
    @is_roblox_staff()
    async def history(self, ctx, type: str):
        """
        View shift history.
        """
        shift_types = await self.bot.shift_types.find_by_id(ctx.guild.id)
        filtered_shift_types = list(shift_types.keys()) if isinstance(shift_types, dict) else ["default"]
        if type not in filtered_shift_types:
            return await ctx.send(
                embed=discord.Embed(
                    title="Invalid Shift Type",
                    description="Please make sure you have selected a valid shift type.",
                    color=RED_COLOR
                )
            )

async def setup(bot):
    await bot.add_cog(ShiftManager(bot))