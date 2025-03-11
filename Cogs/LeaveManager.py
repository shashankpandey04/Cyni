import discord
from discord.ext import commands
from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR, YELLOW_COLOR
from cyni import is_management, is_staff
from discord import app_commands
from utils.utils import time_converter
from utils.pagination import Pagination
from datetime import datetime
from menu import LOARequest

class LeaveManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_loa_embed(self, guild, loa_channel, member, schema, total_past_loas):
        embed = discord.Embed(
            title="LOA Application",
            color=BLANK_COLOR
        ).add_field(
            name="Staff Information",
            value=f"> **Staff Member:** {member.mention}\n> **Past LOAs:** {len(total_past_loas)}",
            inline=False
        ).add_field(
            name="LOA Information",
            value=f"> **Reason:** {schema['reason']}\n> **Start:** <t:{schema['start']}:F>\n> **Expiry:** <t:{schema['expiry']}:F>",
            inline=False
        )
        await loa_channel.send(embed=embed, view=LOARequest(self.bot, guild.id, member.id, schema["_id"]))


    @commands.hybrid_group()
    async def loa(self, ctx):
        """
        Leave of Absence commands.
        """
        pass

    @loa.command(
        name="request",
        extras={
            "category": "Leave of Absence"
        }
    )
    @is_staff()
    @app_commands.describe(time="The duration of the leave of absence 1d/1w/1m")
    @app_commands.describe(reason="The reason for the leave of absence")
    async def request(self, ctx, time: str, reason: str):
        """
        Apply for a leave of absence.
        """
        try:
            duration_seconds = time_converter(time)
        except ValueError:
            return await ctx.send(embed=discord.Embed(
                title="Incorrect Time",
                description="Invalid time format. Please use the following format: `1d/1w/1m`",
                color=RED_COLOR
            ))

        active_loa =  [item async for item in self.bot.loa.db.find({
            "guild_id": ctx.guild.id,
            "user_id": ctx.author.id,
            "accepted": True,
            "denied": False,
            "voided": False,
            "expired": False,
            "type": "loa"
        })]

        if active_loa:
            return await ctx.send(embed=discord.Embed(
                title="Active Leave of Absence",
                description="You already have an active leave of absence.",
                color=RED_COLOR
            ))
        
        total_past_loas = [item async for item in self.bot.loa.db.find({
            "guild_id": ctx.guild.id,
            "user_id": ctx.author.id,
            "type": "loa",
            "accepted": True,
            "denied": False,
        })]
        
        current_timestamp = int(datetime.now().timestamp())
        expiry_timestamp = current_timestamp + duration_seconds

        loa_schema = {
            "guild_id": ctx.guild.id,
            "user_id": ctx.author.id,
            "accepted": False,
            "denied": False,
            "voided": False,
            "expired": False,
            "type": "loa",
            "reason": reason,
            "start": current_timestamp,
            "expiry": expiry_timestamp
        }

        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        loa_channel_id = settings.get("leave_of_absence", {}).get("channel", 1160481898536112170)

        if 0 == loa_channel_id:
            return await ctx.send(embed=discord.Embed(
                title="LOA Channel Not Set",
                description="The leave of absence channel has not been set.",
                color=RED_COLOR
            ))
        await self.bot.loa.db.insert_one(loa_schema)
        await self.send_loa_embed(ctx.guild, ctx.channel, ctx.author, loa_schema, total_past_loas)
        await ctx.send(embed=discord.Embed(
            title="Leave of Absence Requested",
            description="Your leave of absence request has been submitted.",
            color=GREEN_COLOR
        ))

    @loa.command(
        name="view",
        extras={
            "category": "Leave of Absence"
        }
    )
    @is_staff()
    async def view(self, ctx):
        """
        View the all leave of absence applications.
        """
        loas = [item async for item in self.bot.loa.db.find({
            "guild_id": ctx.guild.id,
            "user_id": ctx.author.id,
            "type": "loa"
        })]

        if not loas:
            return await ctx.send(embed=discord.Embed(
                title="No LOAs",
                description="You have no leave of absence requests.",
                color=RED_COLOR
            ))
        
        pages = []
        for loa in loas:
            pages.append(
                discord.Embed(
                    title="LOA Application",
                    color=YELLOW_COLOR
                ).add_field(
                    name="Status",
                    value=(
                        "Accepted" if loa["accepted"] else
                        "Denied" if loa["denied"] else
                        "Voided" if loa["voided"] else
                        "Expired" if loa["expired"] else
                        "Pending"
                    ),
                    inline=False
                ).add_field(
                    name="Reason",
                    value=loa["reason"],
                    inline=True
                ).add_field(
                    name="Start",
                    value=f"<t:{loa['start']}:F>",
                    inline=False
                ).add_field(
                    name="Expiry",
                    value=f"<t:{loa['expiry']}:F>",
                    inline=True
                ).set_author(
                    name=ctx.guild.name,
                    icon_url=ctx.guild.icon
                )
            )

        views = [discord.ui.View() for _ in range(len(pages))]
        view = Pagination(self.bot, ctx.author.id, pages, views)

        await ctx.send(embed=pages[0], view=view)

    @loa.command(
        name="active",
        extras={
            "category": "Leave of Absence"
        }
    )
    @is_management()
    async def active(self, ctx):
        """
        View the active leave of absence applications.
        """

        active_loas = [item async for item in self.bot.loa.db.find({
            "guild_id": ctx.guild.id,
            "accepted": True,
            "denied": False,
            "voided": False,
            "expired": False,
            "type": "loa"
        })]

        if not active_loas:
            return await ctx.send(embed=discord.Embed(
                title="No Active LOAs",
                description="There are no active leave of absence requests.",
                color=RED_COLOR
            ))
        
        pages = []
        for loa in active_loas:
            user = ctx.guild.get_member(loa["user_id"])
            if user is None:
                continue
            pages.append(
                discord.Embed(
                    title=f"LOA Application",
                    color=YELLOW_COLOR
                ).add_field(
                    name="Staff Member",
                    value=user.mention,
                    inline=False
                ).add_field(
                    name="Reason",
                    value=loa["reason"],
                    inline=True
                ).add_field(
                    name="Start",
                    value=f"<t:{loa['start']}:F>",
                    inline=False
                ).add_field(
                    name="Expiry",
                    value=f"<t:{loa['expiry']}:F>",
                    inline=True
                ).set_author(
                    name=ctx.guild.name,
                    icon_url=ctx.guild.icon
                )
            )
        views = [discord.ui.View() for _ in range(len(pages))]
        view = Pagination(self.bot, ctx.author.id, pages, views)
        await ctx.send(embed=pages[0], view=view)

    #@loa.command(
    #    name="admin",
    #    extras={
    #        "category": "Leave of Absence"
    #    }
    #)
    #@is_management()
    #async def admin(self, ctx, user: discord.Member):
    #    """
    #    Admin commands for leave of absence.
    #    """
    #    pass


async def setup(bot):
    await bot.add_cog(LeaveManager(bot))
