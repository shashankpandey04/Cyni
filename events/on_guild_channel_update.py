import os
from dotenv import load_dotenv
import requests
import discord
from discord.ext import commands
from utils.utils import compare_overwrites, discord_time, generate_embed
from utils.constants import YELLOW_COLOR
import datetime
from cyni import premium_check_fun

load_dotenv()

class OnGuildChannelUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_audit_log_entry(self, guild, action=discord.AuditLogAction.channel_update):
        """Get the most recent audit log entry for the specified action."""
        try:
            async for entry in guild.audit_logs(limit=1, action=action):
                return entry
        except discord.Forbidden:
            return None
        return None

    async def _send_log_embed(self, channel, embed):
        """Send an embed to the log channel."""
        try:
            logger = self.bot.get_cog("ThrottledLogger")
            await logger.log_embed(channel, embed)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error sending log embed: {e}")

    def _create_base_embed(self, title, user, channel, created_at):
        """Create a base embed with common fields."""
        user_mention = user.mention if user else "Unknown User"
        return discord.Embed(
            title=title,
            description=f"{user_mention} updated {channel.mention} on {created_at}",
            color=YELLOW_COLOR
        ).set_footer(text=f"Channel ID: {channel.id}")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """
        This event is triggered when a channel is updated in a guild.
        """
        try:
            premium_status = await premium_check_fun(self.bot, before.guild)
            if premium_status in [True] and self.bot.is_premium == False:
                return
            guild = before.guild
            sett = await self.bot.settings.find_by_id(guild.id)
            if not sett:
                return
            
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled") or not moderation_module.get("audit_log"):
                return
                
            guild_log_channel = guild.get_channel(moderation_module.get("audit_log"))
            if not guild_log_channel:
                return

            audit_entry = await self._get_audit_log_entry(guild)
            created_at = discord_time(datetime.datetime.now())

            premium_status = sett.get("premium", False)
            custom_colors = sett.get("customization", {}).get("embed_colors", {}) if premium_status else {}

            if before.name != after.name:
                embed = generate_embed(
                    guild,
                    title="Channel Name Updated",
                    category="logging",
                    description=f"{audit_entry.user.mention if audit_entry else 'Unknown User'} updated {after.mention} on {created_at}",
                    fields=[
                        {"name": "Before", "value": before.name, "inline": True},
                        {"name": "After", "value": after.name, "inline": True},
                        {"name": "Category", "value": str(before.category) if before.category else "None", "inline": False}
                    ],
                    footer=f"Channel ID: {after.id}",
                    premium=premium_status,
                    custom_colors=custom_colors
                )
                # PANEL_URL = os.getenv('PANEL_URL')
                # PANEL_KEY = os.getenv('PANEL_KEY')
                # response = requests.post(
                #     f"{PANEL_URL}/api/v1/panel/channel/update",
                #     headers={"Authorization": f"Bearer {PANEL_KEY}"},
                #     json=after.to_dict()
                # )
                # if response.status_code != 200:
                #     self.bot.logger.error(f"Failed to log channel deletion to panel: {response.status_code} - {response.text}")
                await self._send_log_embed(guild_log_channel, embed)

            if before.category != after.category:
                embed = generate_embed(
                    guild,
                    title="Channel Category Updated",
                    category="logging",
                    description=f"{audit_entry.user.mention if audit_entry else 'Unknown User'} updated {after.mention} on {created_at}",
                    fields=[
                        {"name": "Channel", "value": before.name, "inline": False},
                        {"name": "Before", "value": str(before.category) if before.category else "None", "inline": True},
                        {"name": "After", "value": str(after.category) if after.category else "None", "inline": True}
                    ],
                    footer=f"Channel ID: {after.id}",
                    premium=premium_status,
                    custom_colors=custom_colors
                )
                await self._send_log_embed(guild_log_channel, embed)

            if hasattr(before, 'is_nsfw') and before.is_nsfw() != after.is_nsfw():
                embed = generate_embed(
                    guild,
                    title="Channel NSFW Setting Updated",
                    category="logging",
                    description=f"{audit_entry.user.mention if audit_entry else 'Unknown User'} updated {after.mention} on {created_at}",
                    fields=[
                        {"name": "Channel", "value": before.name, "inline": False},
                        {"name": "Before", "value": f"NSFW: {'Enabled' if before.is_nsfw() else 'Disabled'}", "inline": True},
                        {"name": "After", "value": f"NSFW: {'Enabled' if after.is_nsfw() else 'Disabled'}", "inline": True}
                    ],
                    footer=f"Channel ID: {after.id}",
                    premium=premium_status,
                    custom_colors=custom_colors
                )
                await self._send_log_embed(guild_log_channel, embed)

            if before.overwrites != after.overwrites:
                changes = compare_overwrites(before.overwrites, after.overwrites)
                if changes:
                    human_readable_changes = []
                    for target, perm_type, perm_name, old_value, new_value in changes:
                        target_name = getattr(target, 'name', str(target))
                        old_symbol = "❌" if old_value is False else "✅" if old_value is True else "➖"
                        new_symbol = "❌" if new_value is False else "✅" if new_value is True else "➖"
                        readable_name = perm_name.replace('_', ' ').title()
                        human_readable_changes.append(f"**{target_name}**: {readable_name} ({old_symbol} → {new_symbol})")
                    
                    formatted_changes = "\n".join(human_readable_changes) if human_readable_changes else "No detailed permission changes available"

                    overwrite_entry = await self._get_audit_log_entry(guild, discord.AuditLogAction.overwrite_update)
                    embed = generate_embed(
                        guild,
                        title="Channel Permissions Updated",
                        category="logging",
                        description=f"{overwrite_entry.user.mention if overwrite_entry else 'Unknown User'} updated {after.mention} on {created_at}",
                        fields=[
                            {"name": "Channel", "value": before.name, "inline": False},
                            {"name": "Permission Changes", "value": formatted_changes[:1024], "inline": False}
                        ],
                        footer=f"Channel ID: {after.id}",
                        premium=premium_status,
                        custom_colors=custom_colors
                    )
                    await self._send_log_embed(guild_log_channel, embed)

            if before.type != after.type:
                embed = generate_embed(
                    guild,
                    title="Channel Type Updated",
                    category="logging",
                    description=f"{audit_entry.user.mention if audit_entry else 'Unknown User'} updated {after.mention} on {created_at}",
                    fields=[
                        {"name": "Channel", "value": before.name, "inline": False},
                        {"name": "Before", "value": str(before.type).replace('_', ' ').title(), "inline": True},
                        {"name": "After", "value": str(after.type).replace('_', ' ').title(), "inline": True}
                    ],
                    footer=f"Channel ID: {after.id}",
                    premium=premium_status,
                    custom_colors=custom_colors
                )
                await self._send_log_embed(guild_log_channel, embed)

        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error in on_guild_channel_update: {e}")

async def setup(bot):
    await bot.add_cog(OnGuildChannelUpdate(bot))
