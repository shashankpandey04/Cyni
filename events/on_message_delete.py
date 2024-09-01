import discord
import time
from discord.ext import commands

from utils.constants import RED_COLOR
from utils.utils import discord_time
import datetime

class OnMessageDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """
        This event is triggered when a message is deleted.
        :param message (discord.Message): The message that was deleted.
        """
        
        sett = await self.bot.settings.find_by_id(message.guild.id)
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
        guild_log_channel = message.guild.get_channel(sett["moderation_module"]["audit_log"])
        created_at = discord_time(datetime.datetime.now())
        if message.embeds:
            return
        if message.attachments:
            return
        async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
            embed=discord.Embed(
                    title="Message Deleted",
                    description=f"Message sent by {message.author.mention} was deleted by {entry.user.mention}\n It was deleted {created_at}",
                    color=RED_COLOR
            ).add_field(
                name="Message Content",
                value=message.content,
                inline=False
            ).set_footer(
                text=f"Channel ID: {message.channel.id}"
            )
            await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnMessageDelete(bot))