import discord
import time
from discord.ext import commands

from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
import datetime

class OnMessageEdit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """
        This event is triggered when a message is edited.
        :param before (discord.Message): The message before it was edited.
        :param after (discord.Message): The message after it was edited.
        """
        
        if before.author.bot:
            return
        if before.content == after.content:
            return
        sett = await self.bot.settings.find_by_id(before.guild.id)
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
        guild_log_channel = before.guild.get_channel(sett["moderation_module"]["audit_log"])
        created_at = discord_time(datetime.datetime.now())
        if len(before.content) > 1024:
            before.content = before.content[:1021] + "..."
        if len(after.content) > 1024:
            after.content = after.content[:1021] + "..."
        await guild_log_channel.send(
            embed = discord.Embed(
                title= " ",
                description=f"Message by {before.author.mention} edited on {created_at}",
                color=YELLOW_COLOR
            ).add_field(
                name="Before",
                value=f"{before.content}",
            ).add_field(
                name="After",
                value=f"{after.content}",
            ).set_footer(
                text=f"Message ID: {before.id}"
            )
        )

async def setup(bot):
    await bot.add_cog(OnMessageEdit(bot))