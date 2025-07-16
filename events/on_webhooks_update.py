import discord
from discord.ext import commands
from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
import datetime

class OnWebhookUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_audit_log_entries(self, guild, limit=3):
        """Get recent webhook-related audit log entries."""
        webhook_actions = [
            discord.AuditLogAction.webhook_create,
            discord.AuditLogAction.webhook_update,
            discord.AuditLogAction.webhook_delete
        ]
        
        entries = []
        try:
            for action in webhook_actions:
                async for entry in guild.audit_logs(limit=limit, action=action):
                    # Only include very recent entries (last 10 seconds)
                    time_diff = datetime.datetime.now(datetime.timezone.utc) - entry.created_at
                    if time_diff.total_seconds() <= 10:
                        entries.append(entry)
        except discord.Forbidden:
            return []
        
        # Sort by creation time (most recent first)
        entries.sort(key=lambda x: x.created_at, reverse=True)
        return entries

    async def _send_log_embed(self, channel, embed):
        """Send an embed to the log channel with error handling."""
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error sending webhook update log: {e}")

    def _get_webhook_info(self, entry):
        """Extract webhook information from audit log entry."""
        webhook_info = {
            'name': 'Unknown',
            'avatar': None,
            'channel': None
        }
        
        if hasattr(entry, 'target') and entry.target:
            # Safely get webhook name
            webhook_info['name'] = getattr(entry.target, 'name', 'Unknown')
            
            # Safely get webhook avatar
            if hasattr(entry.target, 'avatar') and entry.target.avatar:
                webhook_info['avatar'] = entry.target.avatar.url
            
            # Safely get webhook channel
            webhook_info['channel'] = getattr(entry.target, 'channel', None)
        
        # For deleted webhooks, try to get info from audit log changes
        if entry.action == discord.AuditLogAction.webhook_delete and hasattr(entry, 'before'):
            if hasattr(entry.before, 'name'):
                webhook_info['name'] = entry.before.name
            if hasattr(entry.before, 'avatar') and entry.before.avatar:
                webhook_info['avatar'] = entry.before.avatar.url
        
        return webhook_info

    def _create_webhook_embed(self, entry, channel, created_at):
        """Create an embed for webhook action."""
        webhook_info = self._get_webhook_info(entry)
        
        action_titles = {
            discord.AuditLogAction.webhook_create: "Webhook Created",
            discord.AuditLogAction.webhook_update: "Webhook Updated",
            discord.AuditLogAction.webhook_delete: "Webhook Deleted"
        }
        
        title = action_titles.get(entry.action, "Webhook Action")
        user_mention = entry.user.mention if entry.user else "Unknown User"
        
        embed = discord.Embed(
            title=title,
            description=f"{user_mention} performed webhook action in {channel.mention} on {created_at}",
            color=YELLOW_COLOR
        ).add_field(
            name="Webhook Name",
            value=webhook_info['name'],
            inline=True
        ).add_field(
            name="Channel",
            value=channel.mention,
            inline=True
        ).add_field(
            name="Action",
            value=title.split()[1].lower(),
            inline=True
        ).set_footer(
            text=f"Channel ID: {channel.id}"
        )
        
        # Add webhook avatar if available
        if webhook_info['avatar']:
            embed.set_thumbnail(url=webhook_info['avatar'])
        
        # Add reason if available
        if entry.reason:
            embed.add_field(
                name="Reason",
                value=entry.reason,
                inline=False
            )
        
        return embed

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        """
        This event is triggered when a channel's webhooks are updated.
        """
        try:
            # Early return checks
            guild = channel.guild
            sett = await self.bot.settings.find_by_id(guild.id)
            if not sett:
                return
            
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled", False) or not moderation_module.get("audit_log"):
                return
                
            guild_log_channel = guild.get_channel(moderation_module["audit_log"])
            if not guild_log_channel:
                return

            # Get recent webhook-related audit log entries
            audit_entries = await self._get_audit_log_entries(guild)
            if not audit_entries:
                return

            created_at = discord_time(datetime.datetime.now())
            
            # Process each relevant audit log entry
            for entry in audit_entries:
                # Check if the entry is related to the channel that triggered the event
                webhook_info = self._get_webhook_info(entry)
                
                # For webhook actions, we need to check if it's related to the channel
                # For deleted webhooks, the channel info might not be available
                is_related_to_channel = False
                
                if webhook_info['channel'] and webhook_info['channel'].id == channel.id:
                    is_related_to_channel = True
                elif entry.action == discord.AuditLogAction.webhook_delete:
                    # For deleted webhooks, check if the audit log extra info matches
                    if hasattr(entry, 'extra') and hasattr(entry.extra, 'channel'):
                        if entry.extra.channel.id == channel.id:
                            is_related_to_channel = True
                
                if is_related_to_channel:
                    embed = self._create_webhook_embed(entry, channel, created_at)
                    await self._send_log_embed(guild_log_channel, embed)
                    break  # Only send one embed per webhook update event
                    
        except Exception as e:
            print(f"Error in on_webhooks_update: {e}")
        
async def setup(bot):
    await bot.add_cog(OnWebhookUpdate(bot))