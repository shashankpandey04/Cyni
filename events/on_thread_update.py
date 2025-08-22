import discord
from discord.ext import commands

from utils.constants import YELLOW_COLOR
from utils.utils import discord_time, generate_embed
from cyni import premium_check_fun
import datetime

class OnThreadUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        """
        This event is triggered when a thread is updated.
        :param before (discord.Thread): The thread before the update.
        :param after (discord.Thread): The thread after the update.
        """

        if after.archived:
            return
        premium_status = await premium_check_fun(self.bot, after.guild)
        if premium_status in [True] and self.bot.is_premium == False:
            return
        sett = await self.bot.settings.find_by_id(after.guild.id)
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
            return
        guild_log_channel = after.guild.get_channel(sett["moderation_module"]["audit_log"])
        if not guild_log_channel:
            return

        created_at = discord_time(datetime.datetime.now())
        async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.thread_update):
            fields = [
                {"name": "Thread Name", "value": after.name, "inline": True},
                {"name": "Created By", "value": f"{entry.user.name}#{entry.user.discriminator} (`{entry.user.id}`)", "inline": True},
                {"name": "Channel", "value": after.parent.mention, "inline": True},
                {"name": "Created At", "value": created_at, "inline": True}
            ]

            if before.applied_tags != after.applied_tags:
                before_tags = [str(tag) for tag in before.applied_tags] if before.applied_tags else []
                after_tags = [str(tag) for tag in after.applied_tags] if after.applied_tags else []
                fields.append({
                    "name": "Applied Tags Changed",
                    "value": f"**Before:** {', '.join(before_tags) or 'None'}\n**After:** {', '.join(after_tags) or 'None'}",
                    "inline": False
                })

            embed = generate_embed(
                guild=after.guild,
                title="Thread Updated",
                description=f"{entry.user.mention} updated {after.mention}",
                category="logging",
                footer=f"Thread ID: {after.id}",
                fields=fields
            )
            logger = self.bot.get_cog("ThrottledLogger")
            await logger.log_embed(guild_log_channel, embed)

async def setup(bot):
    await bot.add_cog(OnThreadUpdate(bot))