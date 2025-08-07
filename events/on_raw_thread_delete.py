import discord
from discord.ext import commands
from utils.constants import YELLOW_COLOR
from utils.utils import discord_time, generate_embed
from cyni import premium_check_fun
import datetime
import io

class OnRawThreadDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_thread_delete(self, payload):
        thread = self.bot.get_channel(payload.thread_id)
        if thread is None:
            return
        premium_status = await premium_check_fun(self.bot, thread.guild)
        if premium_status in [True] and self.bot.is_premium == False:
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

        # Attempt to create transcript
        transcript = io.StringIO()
        try:
            async for msg in thread.history(limit=None, oldest_first=True):
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                author = f"{msg.author.name}#{msg.author.discriminator}"
                content = msg.content
                transcript.write(f"[{timestamp}] {author}: {content}\n")
        except Exception as e:
            transcript.write("Could not fetch messages or thread was already deleted.\n")

        transcript.seek(0)
        file = discord.File(fp=transcript, filename=f"thread-{thread.id}-transcript.txt")

        created_at = discord_time(datetime.datetime.now())
        async for entry in thread.guild.audit_logs(limit=1, action=discord.AuditLogAction.thread_delete):
            embed = generate_embed(
                guild=thread.guild,
                title="Thread Deleted",
                description=f"{entry.user.mention} deleted a thread",
                category="logging",
                footer=f"Thread ID: {thread.id}",
                fields=[
                    {"name": "Thread Name", "value": thread.name, "inline": True},
                    {"name": "Created By", "value": f"{entry.user.name}#{entry.user.discriminator} (`{entry.user.id}`)", "inline": True},
                    {"name": "Channel", "value": thread.parent.mention, "inline": True},
                    {"name": "Created At", "value": created_at, "inline": True}
                ]
            )
            await guild_log_channel.send(embed=embed, file=file)

async def setup(bot):
    await bot.add_cog(OnRawThreadDelete(bot))