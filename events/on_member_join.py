import discord
import time
from discord.ext import commands

from utils.constants import GREEN_COLOR
from utils.utils import discord_time
import datetime

class OnMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        This event is triggered when a member joins a guild.
        :param member (discord.Member): The member that joined the guild.
        """
        
        sett = await self.bot.settings.find_by_id(member.guild.id)
        guild = member.guild
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
        joined_at = discord_time(datetime.datetime.now())
        await guild_log_channel.send(
            embed = discord.Embed(
                title= " ",
                description=f"{member.mention} joined the server on {joined_at}",
                color=GREEN_COLOR
            ).add_field(
                name="Account Created",
                value=f"{discord_time(member.created_at)}",
            ).add_field(
                name="Member Count",
                value=f"{guild.member_count}",
            ).set_author(
                name=member,
                icon_url=member.avatar.url
            ).set_footer(
                text=f"User ID: {member.id}"
            )
        )

async def setup(bot):
    await bot.add_cog(OnMemberJoin(bot))