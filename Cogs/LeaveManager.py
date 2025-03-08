import discord
from discord.ext import commands
from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR, YELLOW_COLOR
from cyni import is_management, is_staff
from discord import app_commands
from utils.utils import log_command_usage, time_converter
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
            "user": ctx.author.id,
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
            "user": ctx.author.id,
            "type": "loa",
            "accepted": True,
            "denied": False,
        })]
        
        current_timestamp = int(datetime.now().timestamp())
        expiry_timestamp = current_timestamp + duration_seconds

        loa_schema = {
            "guild_id": ctx.guild.id,
            "user": ctx.author.id,
            "accepted": False,
            "denied": False,
            "voided": False,
            "expired": False,
            "type": "loa",
            "reason": reason,
            "start": current_timestamp,
            "expiry": expiry_timestamp
        }

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
        View the leave of absence applications.
        """
        if isinstance(ctx, commands.Context):
            await log_command_usage(self.bot, ctx.guild, ctx.author, "Leave of Absence View")

        embed = discord.Embed(
            title="Leave of Absence Applications",
            color=BLANK_COLOR
        )
        embed.description = "No applications."
        await ctx.send(embed=embed)

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
        if isinstance(ctx, commands.Context):
            await log_command_usage(self.bot, ctx.guild, ctx.author, "Leave of Absence Active")

        embed = discord.Embed(
            title="Active Leave of Absence Applications",
            color=BLANK_COLOR
        )
        embed.description = "No active applications."
        await ctx.send(embed=embed)

    @loa.command(
        name="admin",
        extras={
            "category": "Leave of Absence"
        }
    )
    @is_management()
    async def admin(self, ctx, user: discord.Member):
        """
        Admin commands for leave of absence.
        """
        pass


async def setup(bot):
    await bot.add_cog(LeaveManager(bot))
