import discord
from discord.ext import commands
from utils.utils import discord_time, generate_embed
from cyni import premium_check_fun
import datetime
import io

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
            logger = self.bot.get_cog("ThrottledLogger")
            await logger.log_embed(channel, embed)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error sending message delete log: {e}")

    def _should_log_message(self, message):
        """Check if the message should be logged."""
        if message.author.bot or message.webhook_id:
            return False
        
        if message.attachments:
            return True

        if message.content and message.content.strip():
            return True

        return False

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
            if not message.guild:
                return
            premium_status = await premium_check_fun(self.bot, message.guild)
            if premium_status in [True] and self.bot.is_premium == False:
                return
            sett = await self.bot.settings.find_by_id(message.guild.id)
            if not sett:
                return
            
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled", False) or not moderation_module.get("audit_log"):
                return
                
            guild_log_channel = message.guild.get_channel(moderation_module["audit_log"])
            if not guild_log_channel:
                return
            
            if not self._should_log_message(message):
                return

            created_at = discord_time(datetime.datetime.now())
            
            audit_entry = await self._get_audit_log_entry(message.guild, message)
            
            if audit_entry:
                deleter = audit_entry.user
                deletion_type = "by moderator"
                description = f"Message sent by {message.author.mention} was deleted by {deleter.mention} on {created_at}"
            else:
                deleter = message.author
                deletion_type = "self-deleted"
                description = f"Message sent by {message.author.mention} was deleted on {created_at}"
            
            fields = [
                {"name": "Channel", "value": message.channel.mention, "inline": True},
                {"name": "Author", "value": f"{message.author.mention}\n({message.author.name})", "inline": True},
                {"name": "Deletion Type", "value": deletion_type.title(), "inline": True}
            ]
            
            if message.content and message.content.strip():
                fields.append({"name": "Message Content", "value": f"```{self._truncate_content(message.content)}```", "inline": False})
            
            embed = generate_embed(
                guild=message.guild,
                title="Message Deleted",
                category="logging",
                description=description,
                footer=f"Channel ID: {message.channel.id}",
                fields=fields
            )
            
            files_to_send = []
            attachment_info = []
            
            for attachment in message.attachments:
                try:
                    attachment_info.append(f"**{attachment.filename}** ({attachment.size} bytes)")
                
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        if not embed.thumbnail.url:
                            embed.set_thumbnail(url=attachment.url)
                        try:
                            file_bytes = await attachment.read()
                            files_to_send.append(discord.File(fp=io.BytesIO(file_bytes), filename=attachment.filename))
                        except:
                            pass
                    else:
                        try:
                            file_bytes = await attachment.read()
                            files_to_send.append(discord.File(fp=io.BytesIO(file_bytes), filename=attachment.filename))
                        except:
                            pass
                except Exception as e:
                    print(f"Error processing attachment {attachment.filename}: {e}")
            
            if attachment_info:
                embed.add_field(
                    name=f"Attachments ({len(attachment_info)})",
                    value="\n".join(attachment_info[:10]),
                    inline=False
                )

            if not embed.thumbnail.url and message.author.avatar:
                embed.set_thumbnail(url=message.author.avatar.url)
            
            if message.created_at:
                embed.add_field(
                    name="Originally Sent",
                    value=discord_time(message.created_at),
                    inline=True
                )
            
            await self._send_log_embed(guild_log_channel, embed)
            
            for file in files_to_send:
                try:
                    await guild_log_channel.send(file=file)
                except Exception as e:
                    print(f"Error sending attachment file: {e}")
            
        except Exception as e:
            print(f"Error in on_message_delete: {e}")

async def setup(bot):
    await bot.add_cog(OnMessageDelete(bot))