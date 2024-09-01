import discord
import time
from discord.ext import commands

from utils.constants import RED_COLOR
from utils.utils import discord_time
import datetime

class OnMemberUnBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """
        This event is triggered when a member is unbanned from a guild.
        :param guild (discord.Guild): The guild where the member was unbanned.
        :param user (discord.User): The user that was unbanned.
        """
        
        sett = await self.bot.settings.find_by_id(guild.id)
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
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            return await guild_log_channel.send(
                embed = discord.Embed(
                    title= " ",
                    description=f"{entry.user.mention} unbanned {user.mention}\nHe was unbanned {created_at}",
                    color=RED_COLOR
                ).set_footer(
                    text=f"User ID: {user.id}"
                )
            )
async def setup(bot):
    await bot.add_cog(OnMemberUnBan(bot))