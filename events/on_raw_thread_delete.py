import discord
import time
from discord.ext import commands

from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
import datetime

class OnRawThreadDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_thread_delete(self, payload):
        """
        This event is triggered when a thread is deleted.
        :param payload (discord.RawThreadDeleteEvent): The payload that was deleted.
        """
        
        guild = self.bot.get_guild(payload.guild_id)
        sett = await self.bot.settings.find_by_id(payload.guild_id)
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
            return
        guild_log_channel = guild.get_channel(sett.get("moderation_module", {}).get("audit_log"))
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
            cyni_webhook = await guild_log_channel.create_webhook(name="Cyni", avatar=bot_avatar)

        created_at = discord_time(datetime.datetime.now())
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.thread_delete):
            embed = discord.Embed(
                    title= " ",
                    description=f"{entry.user.mention} deleted thread in {entry.channel.mention}\n{created_at}",
                    color=YELLOW_COLOR
                ).set_footer(
                    text=f"Thread ID: {payload.thread_id}"
                )
            if cyni_webhook:
                await cyni_webhook.send(embed=embed)
            else:
                await guild_log_channel.send(embed=embed)

        
async def setup(bot):
    await bot.add_cog(OnRawThreadDelete(bot))