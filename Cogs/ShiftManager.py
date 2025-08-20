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
    @app_commands.autocomplete(shift=shift_type_autocomplete)
    async def manage(self, ctx, shift: str):
        """
        Manage shifts.
        """
        try:
            shift_types = await self.bot.shift_types.find_by_id(ctx.guild.id)
            filtered_shift_types = list(shift_types.keys()) if isinstance(shift_types, dict) else ["default"]
            if shift not in filtered_shift_types:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Invalid Shift Type",
                        description="Please make sure you have selected a valid shift type.",
                        color=RED_COLOR
                    )
                )
            
            active_shift = await self.bot.shift_logs.find(
                {
                    "guild_id": ctx.guild.id,
                    "user_id": ctx.author.id,
                    "type": shift.lower(),
                    "end_epoch": 0
                }
            )
            past_shifts = await self.bot.shift_logs.find(
                {
                    "guild_id": ctx.guild.id,
                    "user_id": ctx.author.id,
                    "type": shift.lower(),
                    "end_epoch": {"$ne": 0}
                }
            )

            view = ShiftManagerView(self.bot, ctx, shift, active_shift, past_shifts)
            await ctx.send(view=view)
            
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred while processing your request: ```{str(e)}```",
                    color=RED_COLOR
                )
            )

    @shift.command(
        name="active",
        aliases=["a"],
    )
    @commands.guild_only()
    @is_roblox_staff()
    @app_commands.autocomplete(shift=shift_type_autocomplete)
    async def active(self, ctx, shift: str):
        """
        View active shifts.
        """
        try:
            shift_types = await self.bot.shift_types.find_by_id(ctx.guild.id)
            filtered_shift_types = list(shift_types.keys()) if isinstance(shift_types, dict) else ["default"]
            if shift not in filtered_shift_types:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Invalid Shift Type",
                        description="Please make sure you have selected a valid shift type.",
                        color=RED_COLOR
                    )
                )

            active_shifts = await self.bot.shift_logs.find(
                {
                    "guild_id": ctx.guild.id,
                    "user_id": ctx.author.id,
                    "type": shift.lower(),
                    "end_epoch": 0
                }
            )

            embed = discord.Embed(
                title=f"{self.bot.emoji.get("folder")} Active Shifts",
                color=BLANK_COLOR
            )
            embed.description = ""
            if active_shifts:
                for i in active_shifts:
                    embed.description += (
                        f"> **User:** <@{i['user_id']}> (`{i['user_id']}`)\n"
                        f"> **Start Time:** <t:{i['start_epoch']}:F>\n"
                        f"> **Shift Type:** {i['type'].capitalize()}\n"
                        f"> **Elapsed Time:** <t:{i['start_epoch']}:R>\n\n"
                    )
            else:
                embed.description = "No active shifts found."

            await ctx.send(embed=embed)
            return
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred while processing your request: ```{str(e)}```",
                    color=RED_COLOR
                )
            )

    @shift.command(
        name="history",
        aliases=["h"],
    )
    @commands.guild_only()
    @is_roblox_staff()
    @app_commands.autocomplete(shift=shift_type_autocomplete)
    async def history(self, ctx, shift: str, user: discord.User = None):
        """
        View shift history.
        """
        try:
            if user is None:
                user = ctx.author
            shift_types = await self.bot.shift_types.find_by_id(ctx.guild.id)
            filtered_shift_types = list(shift_types.keys()) if isinstance(shift_types, dict) else ["default"]
            if shift not in filtered_shift_types:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Invalid Shift Type",
                        description="Please make sure you have selected a valid shift type.",
                        color=RED_COLOR
                    )
                )

            history = await self.bot.shift_logs.find(
                {
                    "guild_id": ctx.guild.id,
                    "user_id": user.id if user else ctx.author.id,
                    "type": shift.lower(),
                    "end_epoch": {"$ne": 0}
                }
            )

            embed = discord.Embed(
                title=f"{self.bot.emoji.get("folder")} Shift History",
                color=BLANK_COLOR
            )
            embed.description = ""
            if history:
                for shift in history:
                    total_duration_seconds = shift.get('duration', 0)
                    hours, remainder = divmod(total_duration_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    total_duration = f"{hours}h {minutes}m {seconds}s" if total_duration_seconds > 0 else "Not Applicable"
                    embed.description += (
                        f"> **Shift Type:** {shift['type'].capitalize()}\n"
                        f"> **Start Time:** <t:{shift['start_epoch']}:F>\n"
                        f"> **End Time:** <t:{shift['end_epoch']}:F>\n"
                        f"> **Duration:** {total_duration}\n\n"
                    )
            else:
                embed.description = "> **No shift history found.**"

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred while processing your request: ```{str(e)}```",
                    color=RED_COLOR
                )
            )

async def setup(bot):
    await bot.add_cog(ShiftManager(bot))