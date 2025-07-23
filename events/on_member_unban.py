import discord
from discord.ext import commands

from utils.constants import RED_COLOR
from utils.utils import discord_time, generate_embed
import datetime
from cyni import premium_check_fun

class OnMemberUnBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """
        This event is triggered when a member is unbanned from a guild.
        :param guild (discord.Guild): The guild where the member was unbanned.
        :param user (discord.User): The user that was unbanned.
        """
        premium_status = await premium_check_fun(self.bot, guild)
        if premium_status in ["use_premium_bot", "use_regular_bot"]:
            return
        sett = await self.bot.settings.find_by_id(guild.id)
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
                return
        guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])
        if not guild_log_channel:
            return

        created_at = discord_time(datetime.datetime.now())
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
            embed = generate_embed(
                guild,
                title="Member Unbanned",
                description=f"{user.mention} was unbanned.",
                category="logging",
                footer=f"User ID: {user.id}",
                fields=[
                    {"name": "Unbanned At", "value": created_at, "inline": True},
                    {"name": "Username", "value": f"{user.name}#{user.discriminator}", "inline": True},
                    {"name": "Moderator", "value": f"{entry.user.mention} (`{entry.user.id}`)", "inline": True}
                ]
            )
            await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnMemberUnBan(bot))