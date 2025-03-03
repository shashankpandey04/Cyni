import discord
import time
from discord.ext import commands

from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
import datetime

class OnWebhookUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        """
        This event is triggered when a channel's webhooks are updated.
        :param channel (discord.TextChannel): The channel whose webhooks were updated.
        """
        
        sett = await self.bot.settings.find_by_id(channel.guild.id)
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
            return
        guild_log_channel = channel.guild.get_channel(sett["moderation_module"]["audit_log"])
        if not guild_log_channel:
            return

        webhooks = await guild_log_channel.webhooks()
        cyni_webhook = None
        for webhook in webhooks:
            if webhook.name == "Cyni":
                cyni_webhook = webhook
                break
        
        if not cyni_webhook:
            bot_avatar = await self.bot.user.avatar.read()
            try:
                cyni_webhook = await guild_log_channel.create_webhook(name="Cyni", avatar=bot_avatar)
            except discord.HTTPException:
                cyni_webhook = None

        created_at = discord_time(datetime.datetime.now())
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_update):
            if entry.action == discord.AuditLogAction.webhook_create:
                title = "Webhook Created"
                description = f"{entry.user.mention} created a webhook in {channel.mention} \n {created_at}"
            elif entry.action == discord.AuditLogAction.webhook_update:
                title = "Webhook Updated"
                description = f"{entry.user.mention} updated a webhook in {channel.mention} \n {created_at}"
            elif entry.action == discord.AuditLogAction.webhook_delete:
                title = "Webhook Deleted"
                description = f"{entry.user.mention} deleted a webhook in {channel.mention} \n {created_at}"
            embed = discord.Embed(
                    title= title,
                    description=description,
                    color=YELLOW_COLOR
                ).set_footer(
                    text=f"Channel ID: {channel.id}"
                )
            if cyni_webhook:
                await cyni_webhook.send(embed=embed)
            else:
                await guild_log_channel.send(embed=embed)
        
async def setup(bot):
    await bot.add_cog(OnWebhookUpdate(bot))