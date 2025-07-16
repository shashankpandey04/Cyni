import discord
from discord.ext import commands
from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
import datetime

class OnGuildRoleUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_audit_log_entry(self, guild, action=discord.AuditLogAction.role_update):
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
            print(f"Error sending role update log: {e}")

    def _create_base_embed(self, title, user, role, created_at):
        """Create a base embed with common fields."""
        user_mention = user.mention if user else "Unknown User"
        return discord.Embed(
            title=title,
            description=f"{user_mention} updated {role.mention} on {created_at}",
            color=YELLOW_COLOR
        ).set_footer(text=f"Role ID: {role.id}")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """
        This event is triggered when a role is updated in a guild.
        """
        try:
            # Early return checks
            guild = after.guild
            sett = await self.bot.settings.find_by_id(guild.id)
            if not sett:
                return
            
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled", False) or not moderation_module.get("audit_log"):
                return
                
            guild_log_channel = guild.get_channel(moderation_module["audit_log"])
            if not guild_log_channel:
                return

            # Get audit log entry once
            audit_entry = await self._get_audit_log_entry(guild)
            created_at = discord_time(datetime.datetime.now())

            # Role name change
            if before.name != after.name:
                embed = self._create_base_embed("Role Name Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(name="Before", value=before.name, inline=True)
                embed.add_field(name="After", value=after.name, inline=True)
                await self._send_log_embed(guild_log_channel, embed)

            # Role color change
            if before.color != after.color:
                embed = self._create_base_embed("Role Color Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(name="Before", value=str(before.color), inline=True)
                embed.add_field(name="After", value=str(after.color), inline=True)
                await self._send_log_embed(guild_log_channel, embed)

            # Role permissions change
            if before.permissions != after.permissions:
                before_perms = [perm for perm, value in before.permissions if value]
                after_perms = [perm for perm, value in after.permissions if value]
                added_perms = set(after_perms) - set(before_perms)
                removed_perms = set(before_perms) - set(after_perms)
                
                embed = self._create_base_embed("Role Permissions Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(
                    name="Added Permissions",
                    value=", ".join(added_perms) if added_perms else "None",
                    inline=False
                )
                embed.add_field(
                    name="Removed Permissions", 
                    value=", ".join(removed_perms) if removed_perms else "None",
                    inline=False
                )
                await self._send_log_embed(guild_log_channel, embed)

            # Role hoist change
            if before.hoist != after.hoist:
                embed = self._create_base_embed("Role Hoist Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(
                    name="Display Separately",
                    value=f"{'Enabled' if before.hoist else 'Disabled'} → {'Enabled' if after.hoist else 'Disabled'}",
                    inline=False
                )
                await self._send_log_embed(guild_log_channel, embed)

            # Role mentionable change
            if before.mentionable != after.mentionable:
                embed = self._create_base_embed("Role Mentionable Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(
                    name="Mentionable",
                    value=f"{'Enabled' if before.mentionable else 'Disabled'} → {'Enabled' if after.mentionable else 'Disabled'}",
                    inline=False
                )
                await self._send_log_embed(guild_log_channel, embed)
                
        except Exception as e:
            print(f"Error in on_guild_role_update: {e}")

async def setup(bot):
    await bot.add_cog(OnGuildRoleUpdate(bot))