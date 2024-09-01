import discord
import time
from discord.ext import commands

from utils.constants import RED_COLOR
from utils.utils import discord_time
import datetime

class OnGuildRoleCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """
        This event is triggered when a role is created in a guild.
        :param role (discord.Role): The role that was created.
        """
        
        sett = await self.bot.settings.find_by_id(role.guild.id)
        guild = role.guild
        if not sett:
            return
        try:
            if not sett["moderation_module"]["enabled"]:
                return
        except KeyError:
            return
        try:
            if not sett["moderation_module"]["enabled"]:
                return
        except KeyError:
            return
        try:
            if not sett["moderation_module"]["audit_log"]:
                return
        except KeyError:
            return
        guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])
        created_at = discord_time(datetime.datetime.now())
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
            return await guild_log_channel.send(
                embed = discord.Embed(
                    title= " ",
                    description=f"{entry.user.mention} created {role.mention} on {created_at}",
                    color=RED_COLOR
                ).set_footer(
                    text=f"Role ID: {role.id}"
                )
            )

async def setup(bot):
    await bot.add_cog(OnGuildRoleCreate(bot))