import discord
from discord.ext import commands
from utils.constants import RED_COLOR
from utils.utils import discord_time, generate_embed
import datetime
from cyni import premium_check_fun

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
            logger = self.bot.get_cog("ThrottledLogger")
            await logger.log_embed(channel, embed)
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
            premium_status = await premium_check_fun(self.bot, channel.guild)
            if premium_status in [True] and self.bot.is_premium == False:
                return
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

            audit_entry = await self._get_audit_log_entry(guild)
            created_at = discord_time(datetime.datetime.now())

            premium_status = sett.get("premium", False)
            custom_colors = sett.get("customization", {}).get("embed_colors", {}) if premium_status else {}

            channel_icon = self._get_channel_type_icon(channel.type)
            channel_type_name = str(channel.type).replace('_', ' ').title()

            user_mention = audit_entry.user.mention if audit_entry else "System"

            embed = generate_embed(
                guild,
                title="Channel Deleted",
                category="logging",
                description=f"{user_mention} deleted **{channel_icon} {channel.name}** on {created_at}",
                footer=f"Channel ID: {channel.id}",
                premium=premium_status,
                custom_colors=custom_colors,
                fields=[
                    {"name": "Channel Type", "value": channel_type_name, "inline": True},
                    {"name": "Channel ID", "value": str(channel.id), "inline": True},
                    {"name": "Category", "value": str(channel.category) if channel.category else "None", "inline": False}
                ]
            )

            if hasattr(channel, 'topic') and channel.topic:
                embed.add_field(
                    name="Topic",
                    value=channel.topic[:1024],
                    inline=False
                )

            if hasattr(channel, 'position'):
                embed.add_field(
                    name="Position",
                    value=str(channel.position),
                    inline=True
                )

            if hasattr(channel, 'is_nsfw') and channel.is_nsfw():
                embed.add_field(
                    name="NSFW",
                    value="Yes",
                    inline=True
                )

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