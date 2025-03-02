import discord
import time
from discord.ext import commands

from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
import datetime

class OnThreadCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        """
        This event is triggered when a thread is created.
        :param thread (discord.Thread): The thread that was created.
        """
        
        if thread.archived:
            return
        sett = await self.bot.settings.find_by_id(thread.guild.id)
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
            return
        guild_log_channel = thread.guild.get_channel(sett["moderation_module"]["audit_log"])

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
        async for entry in thread.guild.audit_logs(limit=1, action=discord.AuditLogAction.thread_create):
            embed = discord.Embed(
                    description=f"{entry.user.mention} created {thread.mention} \n **Channel:** {thread.parent.mention} \n {created_at}",
                    color=YELLOW_COLOR
                ).set_footer(
                    text=f"Thread ID: {thread.id}"
                )
            if cyni_webhook:
                await cyni_webhook.send(embed=embed)
            else:
                await guild_log_channel.send(embed=embed)
        
async def setup(bot):
    await bot.add_cog(OnThreadCreate(bot))