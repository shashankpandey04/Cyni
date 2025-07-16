import discord
from discord.ext import commands
from utils.constants import RED_COLOR
from utils.utils import discord_time
import datetime

class OnMessageDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_audit_log_entry(self, guild, target_message):
        """Get the most recent audit log entry for message deletion with better accuracy."""
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
                # Check if the audit log entry matches our deleted message
                if (entry.target.id == target_message.author.id and 
                    hasattr(entry.extra, 'channel') and 
                    entry.extra.channel.id == target_message.channel.id):
                    # Check if the timing is reasonable (within last 5 seconds)
                    time_diff = datetime.datetime.now(datetime.timezone.utc) - entry.created_at
                    if time_diff.total_seconds() <= 5:
                        return entry
        except (discord.Forbidden, AttributeError):
            pass
        return None

    async def _send_log_embed(self, channel, embed):
        """Send an embed to the log channel with error handling."""
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error sending message delete log: {e}")

    def _should_log_message(self, message):
        """Check if the message should be logged."""
        # Skip if message has embeds or attachments (these are usually bot messages)
        if message.embeds or message.attachments:
            return False
        
        # Skip if message is empty
        if not message.content or not message.content.strip():
            return False
            
        # Skip if message is from a bot
        if message.author.bot:
            return False
            
        # Skip if message is from a webhook
        if message.webhook_id:
            return False
            
        return True

    def _truncate_content(self, content, max_length=1000):
        """Truncate message content if it's too long."""
        if len(content) > max_length:
            return content[:max_length] + "..."
        return content

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """
        This event is triggered when a message is deleted.
        """
        try:
            # Skip if message is not in a guild
            if not message.guild:
                return
                
            # Early return checks
            sett = await self.bot.settings.find_by_id(message.guild.id)
            if not sett:
                return
            
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled", False) or not moderation_module.get("audit_log"):
                return
                
            guild_log_channel = message.guild.get_channel(moderation_module["audit_log"])
            if not guild_log_channel:
                return

            # Check if we should log this message
            if not self._should_log_message(message):
                return

            created_at = discord_time(datetime.datetime.now())
            
            # Get audit log entry with better accuracy
            audit_entry = await self._get_audit_log_entry(message.guild, message)
            
            # Determine who deleted the message
            if audit_entry:
                # Message was deleted by a moderator
                deleter = audit_entry.user
                deletion_type = "by moderator"
                description = f"Message sent by {message.author.mention} was deleted by {deleter.mention} on {created_at}"
            else:
                # Message was likely self-deleted or bulk deleted
                deleter = message.author
                deletion_type = "self-deleted"
                description = f"Message sent by {message.author.mention} was deleted on {created_at}"
            
            # Create embed
            embed = discord.Embed(
                title="Message Deleted",
                description=description,
                color=RED_COLOR
            ).add_field(
                name="Channel",
                value=message.channel.mention,
                inline=True
            ).add_field(
                name="Author",
                value=f"{message.author.mention}\n({message.author.name})",
                inline=True
            ).add_field(
                name="Deletion Type",
                value=deletion_type.title(),
                inline=True
            ).add_field(
                name="Message Content",
                value=f"```{self._truncate_content(message.content)}```",
                inline=False
            ).set_footer(
                text=f"Message ID: {message.id} • Channel ID: {message.channel.id}"
            )
            
            # Add message author avatar
            if message.author.avatar:
                embed.set_thumbnail(url=message.author.avatar.url)
            
            # Add timestamp when message was originally sent
            if message.created_at:
                embed.add_field(
                    name="Originally Sent",
                    value=discord_time(message.created_at),
                    inline=True
                )
            
            await self._send_log_embed(guild_log_channel, embed)
            
        except Exception as e:
            print(f"Error in on_message_delete: {e}")

async def setup(bot):
    await bot.add_cog(OnMessageDelete(bot))