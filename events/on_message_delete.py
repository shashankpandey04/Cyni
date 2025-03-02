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
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
            return
        guild_log_channel = message.guild.get_channel(sett["moderation_module"]["audit_log"])
        if not guild_log_channel:
            return
        created_at = discord_time(datetime.datetime.now())
        if message.embeds:
            return
        if message.attachments:
            return
        
        webhooks = await guild_log_channel.webhooks()
        cyni_webhook = None
        for webhook in webhooks:
            if webhook.name == "Cyni":
                cyni_webhook = webhook
            break
        
        if not cyni_webhook:
            bot_avatar = await self.bot.user.avatar.read()
            cyni_webhook = await guild_log_channel.create_webhook(name="Cyni", avatar=bot_avatar)
        
        async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
            embed = discord.Embed(
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
            
            if cyni_webhook:
                await cyni_webhook.send(embed=embed)
            else:
                await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnMessageDelete(bot))