import discord
from discord.ext import commands
from utils.constants import RED_COLOR
from utils.utils import discord_time
import datetime

class OnGuildRoleDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_audit_log_entry(self, guild, action=discord.AuditLogAction.role_delete):
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
            print(f"Error sending role delete log: {e}")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """
        This event is triggered when a role is deleted in a guild.
        """
        try:
            # Early return checks
            guild = role.guild
            sett = await self.bot.settings.find_by_id(guild.id)
            if not sett:
                return
            
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled", False) or not moderation_module.get("audit_log"):
                return
                
            guild_log_channel = guild.get_channel(moderation_module["audit_log"])
            if not guild_log_channel:
                return

            # Get audit log entry
            audit_entry = await self._get_audit_log_entry(guild)
            created_at = discord_time(datetime.datetime.now())
            
            # Create and send embed
            user_mention = audit_entry.user.mention if audit_entry else "Unknown User"
            embed = discord.Embed(
                title="Role Deleted",
                description=f"{user_mention} deleted **{role.name}** on {created_at}",
                color=RED_COLOR
            ).add_field(
                name="Role Information",
                value=f"**Name:** {role.name}\n**Color:** {role.color}\n**Position:** {role.position}\n**Members:** {len(role.members)}",
                inline=False
            ).set_footer(
                text=f"Role ID: {role.id}"
            )

            await self._send_log_embed(guild_log_channel, embed)
            
        except Exception as e:
            print(f"Error in on_guild_role_delete: {e}")

async def setup(bot):
    await bot.add_cog(OnGuildRoleDelete(bot))