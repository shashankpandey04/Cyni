import discord
import datetime
from discord.ext import commands
from utils.constants import RED_COLOR
from utils.utils import discord_time

class OnMemberBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_audit_log_entry(self, guild, action=discord.AuditLogAction.ban):
        """Get the most recent audit log entry for the specified action."""
        try:
            async for entry in guild.audit_logs(limit=1, action=action):
                return entry
        except discord.Forbidden:
            return None
        return None

    async def _send_log_embed(self, channel, embed):
        """Send an embed to the log channel with error handling."""
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error sending ban log: {e}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """
        This event is triggered when a member is banned from a guild.
        """
        try:
            # Early return checks
            sett = await self.bot.settings.find_by_id(guild.id)
            if not sett:
                return
                
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled", False) or not moderation_module.get("audit_log"):
                return
                
            guild_log_channel = guild.get_channel(moderation_module.get("audit_log"))
            if not guild_log_channel:
                return

            # Get ban information from audit logs
            ban_entry = await self._get_audit_log_entry(guild)
            if not ban_entry:
                return

            # Build and send embed
            created_at = discord_time(datetime.datetime.now())
            
            embed = discord.Embed(
                title="Member Banned",
                description=f"{ban_entry.user.mention} banned {user.mention} on {created_at}",
                color=RED_COLOR
            ).add_field(
                name="Banned User",
                value=f"**Username:** {user.name}\n**ID:** {user.id}\n**Mention:** {user.mention}",
                inline=False
            ).add_field(
                name="Banned By",
                value=f"**Username:** {ban_entry.user.name}\n**ID:** {ban_entry.user.id}",
                inline=False
            ).set_footer(text=f"User ID: {user.id}")
            
            # Add ban reason if available
            if ban_entry.reason:
                embed.add_field(
                    name="Reason",
                    value=ban_entry.reason,
                    inline=False
                )
            
            # Add user avatar if available
            if user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
            
            await self._send_log_embed(guild_log_channel, embed)
            
        except Exception as e:
            print(f"Error in on_member_ban: {e}")


async def setup(bot):
    await bot.add_cog(OnMemberBan(bot))