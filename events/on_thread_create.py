import discord
from discord.ext import commands

from utils.constants import YELLOW_COLOR
from utils.utils import discord_time, generate_embed
from cyni import premium_check_fun
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
        premium_status = await premium_check_fun(self.bot, thread.guild)
        if premium_status in ["use_premium_bot", "use_regular_bot"]:
            return
        sett = await self.bot.settings.find_by_id(thread.guild.id)
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
            return
        guild_log_channel = thread.guild.get_channel(sett["moderation_module"]["audit_log"])
        if not guild_log_channel:
            return

        created_at = discord_time(datetime.datetime.now())
        async for entry in thread.guild.audit_logs(limit=1, action=discord.AuditLogAction.thread_create):
            embed = await generate_embed(
                guild=thread.guild,
                title="Thread Created",
                description=f"{entry.user.mention} created {thread.mention}",
                category="logging",
                footer=f"Thread ID: {thread.id}",
                fields=[
                    {"name": "Thread Name", "value": thread.name, "inline": True},
                    {"name": "Created By", "value": f"{entry.user.name}#{entry.user.discriminator} (`{entry.user.id}`)", "inline": True},
                    {"name": "Channel", "value": thread.parent.mention, "inline": True},
                    {"name": "Created At", "value": created_at, "inline": True}
                ]
            )
            await guild_log_channel.send(embed=embed)
        
async def setup(bot):
    await bot.add_cog(OnThreadCreate(bot))