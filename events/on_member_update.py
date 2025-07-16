import discord
from discord.ext import commands
from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
import datetime

class OnMemberUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_audit_log_entry(self, guild, action):
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
            print(f"Error sending member update log: {e}")

    def _create_base_embed(self, description, user, member, created_at):
        """Create a base embed with common fields."""
        return discord.Embed(
            description=description,
            color=YELLOW_COLOR
        ).set_author(
            name=str(member),
            icon_url=member.avatar.url if member.avatar else None
        ).set_footer(
            text=f"User ID: {member.id}"
        )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """
        This event is triggered when a member's information is updated.
        """
        try:
            # Early return checks
            guild = before.guild
            sett = await self.bot.settings.find_by_id(guild.id)
            if not sett:
                return
            
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled", False) or not moderation_module.get("audit_log"):
                return
                
            guild_log_channel = guild.get_channel(moderation_module["audit_log"])
            if not guild_log_channel:
                return

            created_at = discord_time(datetime.datetime.now())
            
            # Handle nickname changes
            if before.nick != after.nick:
                await self._handle_nickname_change(before, after, guild, guild_log_channel, created_at)
                
            # Handle role changes
            if before.roles != after.roles:
                await self._handle_role_changes(before, after, guild, guild_log_channel, created_at)
                
        except Exception as e:
            print(f"Error in on_member_update: {e}")

    async def _handle_nickname_change(self, before, after, guild, guild_log_channel, created_at):
        """Handle nickname change logging."""
        audit_entry = await self._get_audit_log_entry(guild, discord.AuditLogAction.member_update)
        user_mention = audit_entry.user.mention if audit_entry else "Unknown User"
        
        before_nick = before.nick or "None"
        after_nick = after.nick or "None"
        
        description = f"{user_mention} updated {before.mention}'s nickname on {created_at}"
        embed = self._create_base_embed(description, audit_entry.user if audit_entry else None, before, created_at)
        embed.add_field(
            name="Nickname Change",
            value=f"**Before:** {before_nick}\n**After:** {after_nick}",
            inline=False
        )
        
        await self._send_log_embed(guild_log_channel, embed)

    async def _handle_role_changes(self, before, after, guild, guild_log_channel, created_at):
        """Handle role change logging."""
        role_added = [role for role in after.roles if role not in before.roles]
        role_removed = [role for role in before.roles if role not in after.roles]
        
        if role_added:
            audit_entry = await self._get_audit_log_entry(guild, discord.AuditLogAction.member_role_update)
            user_mention = audit_entry.user.mention if audit_entry else "Unknown User"
            
            role_mentions = [role.mention for role in role_added]
            description = f"{user_mention} added {', '.join(role_mentions)} to {before.mention} on {created_at}"
            embed = self._create_base_embed(description, audit_entry.user if audit_entry else None, before, created_at)
            embed.add_field(
                name="Roles Added",
                value=', '.join(role_mentions),
                inline=False
            )
            
            await self._send_log_embed(guild_log_channel, embed)
                    
        if role_removed:
            audit_entry = await self._get_audit_log_entry(guild, discord.AuditLogAction.member_role_update)
            user_mention = audit_entry.user.mention if audit_entry else "Unknown User"
            
            role_mentions = [role.mention for role in role_removed]
            description = f"{user_mention} removed {', '.join(role_mentions)} from {before.mention} on {created_at}"
            embed = self._create_base_embed(description, audit_entry.user if audit_entry else None, before, created_at)
            embed.add_field(
                name="Roles Removed",
                value=', '.join(role_mentions),
                inline=False
            )
            
            await self._send_log_embed(guild_log_channel, embed)

async def setup(bot):
    await bot.add_cog(OnMemberUpdate(bot))