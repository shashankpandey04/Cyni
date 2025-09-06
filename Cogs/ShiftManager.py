import discord
from discord.ext import commands
import time

from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR, YELLOW_COLOR
from discord import app_commands
from cyni import is_roblox_management, is_roblox_staff, roblox_management_check, roblox_management_check
from utils.utils import log_command_usage
from utils.autocompletes import shift_type_autocomplete
from Views.ShiftManager import *
from utils.basic_pager import BasicPager


class ShiftManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# Shift Type Doc
# {
#   "_id": {
#     "$numberLong": "1228305781938720779"
#   },
#   "test": {
#     "access_role": [
#       {
#         "$numberLong": "1236184696417816636"
#       },
#       {
#         "$numberLong": "1236184610224738404"
#       }
#     ]
#   },
#   "Affiliate": {
#     "access_role": [
#       {
#         "$numberLong": "1236184656261677066"
#       }
#     ]
#   }
# }
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
            
            if shift != "default":
                user_roles = [role.id for role in ctx.author.roles]
                shift_access_roles = shift_types.get(shift, {}).get("access_role", [])
                if not any(role in user_roles for role in shift_access_roles):
                    return await ctx.send(
                        embed=discord.Embed(
                            title="Access Denied",
                            description="You do not have permission to manage this shift.",
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

            if shift != "default":
                user_roles = [role.id for role in ctx.author.roles]
                shift_access_roles = shift_types.get(shift, {}).get("access_role", [])
                if not any(role in user_roles for role in shift_access_roles):
                    return await ctx.send(
                        embed=discord.Embed(
                            title="Access Denied",
                            description="You do not have permission to manage this shift.",
                            color=RED_COLOR
                        )
                    )

            active_shifts = await self.bot.shift_logs.find(
                {
                    "guild_id": ctx.guild.id,
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

            if shift != "default":
                user_roles = [role.id for role in ctx.author.roles]
                shift_access_roles = shift_types.get(shift, {}).get("access_role", [])
                if not any(role in user_roles for role in shift_access_roles):
                    return await ctx.send(
                        embed=discord.Embed(
                            title="Access Denied",
                            description="You do not have permission to manage this shift.",
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
                    removed_time = shift.get("removed_time", 0)
                    total_duration_seconds = shift.get('duration', 0)
                    total_duration_seconds -= removed_time
                    added_time = shift.get("added_time", 0)
                    total_duration_seconds = max(0, total_duration_seconds + added_time - removed_time)

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

    @shift.command(
        name="leaderboard",
        description="View the shift leaderboard."
    )
    @commands.guild_only()
    @is_roblox_staff()
    @app_commands.autocomplete(shift=shift_type_autocomplete)
    async def leaderboard(self, ctx, shift: str):
        """
        View the shift leaderboard.
        """
        try:
            await ctx.typing()
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
            
            if shift != "default":
                user_roles = [role.id for role in ctx.author.roles]
                shift_access_roles = shift_types.get(shift, {}).get("access_role", [])
                if not any(role in user_roles for role in shift_access_roles):
                    return await ctx.send(
                        embed=discord.Embed(
                            title="Access Denied",
                            description="You do not have permission to manage this shift.",
                            color=RED_COLOR
                        )
                    )
                
            leaderboard_data = await self.bot.shift_logs.aggregate([
                {
                    "$match": {
                        "guild_id": ctx.guild.id,
                        "end_epoch": {"$ne": 0},
                        "type": shift.lower()
                    }
                },
                {
                    "$group": {
                        "_id": "$user_id",
                        "total_duration": {"$sum": "$duration"}
                    }
                },
                {
                    "$sort": {"total_duration": -1}
                },
                {
                    "$limit": 10
                }
            ])

            if not leaderboard_data:
                return await ctx.send(
                    embed=discord.Embed(
                        title="No Data",
                        description="No shift data found for the specified shift type.",
                        color=RED_COLOR
                    )
                )

            embeds = []
            embed = discord.Embed(
                title=f"{self.bot.emoji.get('trophy')} Shift Leaderboard",
                color=BLANK_COLOR
            )
            embed.description = ""
            if leaderboard_data:
                for i, entry in enumerate(leaderboard_data, start=1):
                    user = await self.bot.fetch_user(entry["_id"])
                    total_duration = entry["total_duration"]
                    hours, remainder = divmod(total_duration, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    total_duration_str = f"{hours}h {minutes}m {seconds}s" if total_duration > 0 else "Not Applicable"
                    embed.description += (
                        f"> **#{i} {user.name}** (`{user.id}`)\n"
                        f"> **Total Duration:** {total_duration_str}\n\n"
                    )
                    
                    if i % 25 == 0:
                        embeds.append(embed)
                        embed = discord.Embed(
                            title=f"{self.bot.emoji.get('trophy')} Shift Leaderboard (Continued)",
                            color=BLANK_COLOR
                        )
                        embed.description = ""
                
                if embed.description:
                    embeds.append(embed)
            else:
                embed.description = "> **No shift data found.**"
                embeds.append(embed)

            button_view = discord.ui.View()
            url_button = discord.ui.Button(
                label="View Spreadsheet",
                url=f"https://cyni.quprdigital.tk/spreadsheet/shifts/{ctx.guild.id}/{shift.lower()}",
                style=discord.ButtonStyle.url,
                row=1
            )
            button_view.add_item(url_button)
            pager = BasicPager(
                user_id=ctx.author.id,
                embeds=embeds,
                view=button_view
            )
            await ctx.send(embed=embeds[0], view=pager)

        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred while processing your request: ```{str(e)}```",
                    color=RED_COLOR
                )
            )

    @shift.command(
        name="reset",
        description="Reset the shift leaderboard."
    )
    @commands.guild_only()
    @is_roblox_management()
    @app_commands.autocomplete(shift=shift_type_autocomplete)
    async def reset(self, ctx, shift: str):
        """
        Reset the shift leaderboard.
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

            if shift != "default":
                user_roles = [role.id for role in ctx.author.roles]
                shift_access_roles = shift_types.get(shift, {}).get("access_role", [])
                if not any(role in user_roles for role in shift_access_roles):
                    return await ctx.send(
                        embed=discord.Embed(
                            title="Access Denied",
                            description="You do not have permission to manage this shift.",
                            color=RED_COLOR
                        )
                    )

            view = ShiftLeaderBoardMenu(self.bot, ctx, shift)
            await ctx.send(
                embed=discord.Embed(
                    title="Shift Leaderboard Reset",
                    description="The shift leaderboard has been reset.",
                    color=BLANK_COLOR
                ),
                view=view
            )
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred while processing your request: ```{str(e)}```",
                    color=RED_COLOR
                )
            )
        
    @shift.command(
        name="admin",
        description="Administrative shift commands."
    )
    @commands.guild_only()
    @is_roblox_management()
    @app_commands.autocomplete(shift=shift_type_autocomplete)
    async def admin(self, ctx, user: discord.User, shift: str,):
        """
        Administrative shift commands.
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
                    "user_id": user.id,
                    "type": shift.lower(),
                    "end_epoch": 0
                }
            )
            past_shifts = await self.bot.shift_logs.find(
                {
                    "guild_id": ctx.guild.id,
                    "user_id": user.id,
                    "type": shift.lower(),
                    "end_epoch": {"$ne": 0}
                }
            )

            total_shift_duration_seconds = sum(shift.get('duration', 0) for shift in past_shifts) if past_shifts else 0
            removed_time = sum(shift.get("removed_time", 0) for shift in past_shifts) if past_shifts else 0
            total_shift_duration_seconds -= removed_time
            added_time = sum(shift.get("added_time", 0) for shift in past_shifts) if past_shifts else 0
            total_shift_duration_seconds = max(0, total_shift_duration_seconds + added_time - removed_time)

            hours, remainder = divmod(total_shift_duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            total_shift_duration = f"{hours}h {minutes}m {seconds}s" if total_shift_duration_seconds > 0 else "Not Applicable"

            embed = discord.Embed(
                title=" ",
                color=BLANK_COLOR
            ).add_field(
                name="Staff Information",
                value=(
                    f"> **User:** {ctx.author.mention} (`{ctx.author.id}`)\n"
                    f"> **Shift Type:** {shift.capitalize()}\n"
                    f"> **Past Shifts:** {len(past_shifts)}\n"
                    f"> **Total Past Duration:** {total_shift_duration}\n\n"
                ),
                inline=False
            )

            if active_shift:
                if active_shift:
                    embed.add_field(
                        name="Current Shift",
                        value=(
                            f"> **Start:** <t:{int(active_shift[0]['start_epoch'])}:T>\n"
                            f"> **Breaks Taken:** {len(active_shift[0].get('breaks', []))}\n"
                        ),
                        inline=False
                    )
            status = "offduty"
            shift_data = None
            
            if active_shift:
                shift_data = active_shift[0] if len(active_shift) > 0 else {}
                
                if shift_data:
                    status = "onduty"
                    breaks = shift_data.get("breaks", [])

                    if breaks:
                        for b in breaks:
                            if isinstance(b, dict):
                                if b.get("end_epoch", 0) == 0:
                                    status = "onbreak"
                                    break
                            elif isinstance(b, list) and len(b) > 1:
                                if len(b) < 2 or b[1] == 0:
                                    status = "onbreak"
                                    break
                
            embed.set_footer(text=f"Managing shifts for {user} | User ID: {user.id}")
            embed.set_thumbnail(
                url=user.display_avatar.url
            )

            if status == "onduty":
                embed.color = GREEN_COLOR
                embed.title = f"{self.bot.emoji.get('onshift')} On-Duty"
            elif status == "onbreak":
                embed.color = YELLOW_COLOR
                embed.title = f"{self.bot.emoji.get('shiftbreak')} On Break"
            else:
                embed.color = RED_COLOR
                embed.title = f"{self.bot.emoji.get('offshift')} Off Duty"

            view = ShiftAdminView(self.bot, ctx, user, shift, active_shift, past_shifts, status)
            await ctx.send(embed=embed, view=view)

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
