import discord
import time
from discord.ext import commands

from utils.constants import RED_COLOR
from utils.utils import discord_time
import datetime

class OnMemberRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """
        This event is triggered when a member leaves a guild.
        :param member (discord.Member): The member that left the guild.
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
        left_at = discord_time(datetime.datetime.now())
        await guild_log_channel.send(
            embed = discord.Embed(
                title= " ",
                description=f"{member.mention} left the server on {left_at}",
                color=RED_COLOR
            ).add_field(
                name="Member Count",
                value=f"{guild.member_count}",
            ).set_author(
                name=member,
                icon_url=member.avatar.url
            ).set_footer(
                text=f"User ID: {member.id}"
            ).set_thumbnail(
                url=member.avatar.url
            )
        )

async def setup(bot):
    await bot.add_cog(OnMemberRemove(bot))