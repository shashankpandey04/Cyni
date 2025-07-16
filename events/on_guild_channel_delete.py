import discord
from discord.ext import commands
from utils.constants import RED_COLOR
from utils.utils import discord_time
import datetime

class OnGuildChannelDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_audit_log_entry(self, guild, action=discord.AuditLogAction.channel_delete):
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
            print(f"Error sending channel delete log: {e}")

    def _get_channel_type_icon(self, channel_type):
        """Get an icon for the channel type."""
        type_icons = {
            discord.ChannelType.text: "💬",
            discord.ChannelType.voice: "🔊",
            discord.ChannelType.category: "📁",
            discord.ChannelType.news: "📰",
            discord.ChannelType.stage_voice: "🎙️",
            discord.ChannelType.forum: "💭",
            discord.ChannelType.news_thread: "🧵",
            discord.ChannelType.public_thread: "🧵",
            discord.ChannelType.private_thread: "🔒"
        }
        return type_icons.get(channel_type, "❓")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """
        This event is triggered when a channel is deleted in a guild.
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

            # Get audit log entry
            audit_entry = await self._get_audit_log_entry(guild)
            created_at = discord_time(datetime.datetime.now())
            
            # Get channel information before it's deleted
            channel_icon = self._get_channel_type_icon(channel.type)
            channel_type_name = str(channel.type).replace('_', ' ').title()
            
            # Create embed with proper channel name (not mention since it's deleted)
            user_mention = audit_entry.user.mention if audit_entry else "Unknown User"
            
            embed = discord.Embed(
                title="Channel Deleted",
                description=f"{user_mention} deleted **{channel_icon} {channel.name}** on {created_at}",
                color=RED_COLOR
            ).add_field(
                name="Channel Information",
                value=f"**Name:** {channel.name}\n**Type:** {channel_type_name}\n**Category:** {channel.category.name if channel.category else 'None'}",
                inline=False
            ).set_footer(
                text=f"Channel ID: {channel.id}"
            )
            
            # Add additional information based on channel type
            if hasattr(channel, 'topic') and channel.topic:
                embed.add_field(
                    name="Topic",
                    value=channel.topic[:1024],  # Limit to prevent embed field length errors
                    inline=False
                )
            
            # Add position information
            if hasattr(channel, 'position'):
                embed.add_field(
                    name="Position",
                    value=str(channel.position),
                    inline=True
                )
            
            # Add NSFW status for text channels
            if hasattr(channel, 'is_nsfw') and channel.is_nsfw():
                embed.add_field(
                    name="NSFW",
                    value="Yes",
                    inline=True
                )
            
            # Add reason if available in audit log
            if audit_entry and audit_entry.reason:
                embed.add_field(
                    name="Reason",
                    value=audit_entry.reason,
                    inline=False
                )
            
            await self._send_log_embed(guild_log_channel, embed)
            
        except Exception as e:
            print(f"Error in on_guild_channel_delete: {e}")

async def setup(bot):
    await bot.add_cog(OnGuildChannelDelete(bot))