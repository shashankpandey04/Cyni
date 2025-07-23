import discord
from discord.ext import commands
from utils.constants import YELLOW_COLOR
from utils.utils import discord_time, generate_embed
import datetime
from cyni import premium_check_fun

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

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """
        This event is triggered when a member's information is updated.
        """
        try:
            guild = before.guild
            premium_status = await premium_check_fun(self.bot, guild)
            if premium_status in ["use_premium_bot", "use_regular_bot"]:
                return
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
            
            if before.nick != after.nick:
                await self._handle_nickname_change(before, after, guild, guild_log_channel, created_at)

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
        
        embed = await generate_embed(
            guild,
            title="Nickname Changed",
            category="logging",
            description=f"{user_mention} updated {before.mention}'s nickname on {created_at}",
            footer=f"User ID: {before.id}",
            fields=[
                {"name": "Before", "value": before_nick, "inline": True},
                {"name": "After", "value": after_nick, "inline": True},
                {"name": "Username", "value": f"{before.name} (`{before.id}`)", "inline": True}
            ]
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
            embed = await generate_embed(
                guild,
                title="Role Added",
                category="logging",
                description=f"Added {', '.join(role_mentions)} to {before.mention}",
                footer=f"User ID: {before.id}",
                fields=[
                    {"name": "Roles Added", "value": ', '.join(role_mentions), "inline": False},
                    {"name": "Username", "value": f"{before.name}#{before.discriminator}", "inline": True},
                    {"name": "Added By", "value": f"{user_mention} (`{audit_entry.user.id}`)" if audit_entry else "Unknown User", "inline": True},
                    {"name": "Timestamp", "value": created_at, "inline": True}
                ]
            )
            
            await self._send_log_embed(guild_log_channel, embed)
                    
        if role_removed:
            audit_entry = await self._get_audit_log_entry(guild, discord.AuditLogAction.member_role_update)
            user_mention = audit_entry.user.mention if audit_entry else "Unknown User"
            
            role_mentions = [role.mention for role in role_removed]
            embed = await generate_embed(
                guild,
                title="Role Removed",
                category="logging",
                description=f"Removed {', '.join(role_mentions)} from {before.mention}",
                footer=f"User ID: {before.id}",
                fields=[
                    {"name": "Roles Removed", "value": ', '.join(role_mentions), "inline": False},
                    {"name": "Username", "value": f"{before.name}#{before.discriminator}", "inline": True},
                    {"name": "Removed By", "value": f"{user_mention} (`{audit_entry.user.id}`)" if audit_entry else "Unknown User", "inline": True},
                    {"name": "Timestamp", "value": created_at, "inline": True}
                ]
            )
            
            await self._send_log_embed(guild_log_channel, embed)

async def setup(bot):
    await bot.add_cog(OnMemberUpdate(bot))