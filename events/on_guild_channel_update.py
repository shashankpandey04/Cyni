import discord
from discord.ext import commands
from utils.utils import compare_overwrites, discord_time
from utils.constants import YELLOW_COLOR
import datetime

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
            await channel.send(embed=embed)
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
            # Early return checks
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

            # Get audit log entry once
            audit_entry = await self._get_audit_log_entry(guild)
            created_at = discord_time(datetime.datetime.now())

            # Channel name change
            if before.name != after.name:
                embed = self._create_base_embed("Channel Name Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(name="Before", value=before.name, inline=True)
                embed.add_field(name="After", value=after.name, inline=True)
                embed.add_field(name="Category", value=str(before.category) if before.category else "None", inline=False)
                await self._send_log_embed(guild_log_channel, embed)

            # Channel category change
            if before.category != after.category:
                embed = self._create_base_embed("Channel Category Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(name="Channel", value=before.name, inline=False)
                embed.add_field(name="Before", value=str(before.category) if before.category else "None", inline=True)
                embed.add_field(name="After", value=str(after.category) if after.category else "None", inline=True)
                await self._send_log_embed(guild_log_channel, embed)

            # NSFW setting change
            if hasattr(before, 'is_nsfw') and before.is_nsfw() != after.is_nsfw():
                embed = self._create_base_embed("Channel NSFW Setting Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(name="Channel", value=before.name, inline=False)
                embed.add_field(name="Before", value=f"NSFW: {'Enabled' if before.is_nsfw() else 'Disabled'}", inline=True)
                embed.add_field(name="After", value=f"NSFW: {'Enabled' if after.is_nsfw() else 'Disabled'}", inline=True)
                await self._send_log_embed(guild_log_channel, embed)

            # Permission overwrites change
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
                    
                    # Get specific overwrite audit log entry
                    overwrite_entry = await self._get_audit_log_entry(guild, discord.AuditLogAction.overwrite_update)
                    embed = self._create_base_embed("Channel Permissions Updated", overwrite_entry.user if overwrite_entry else None, after, created_at)
                    embed.add_field(name="Channel", value=before.name, inline=False)
                    embed.add_field(name="Permission Changes", value=formatted_changes[:1024], inline=False)  # Limit field length
                    await self._send_log_embed(guild_log_channel, embed)

            # Channel type change
            if before.type != after.type:
                embed = self._create_base_embed("Channel Type Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(name="Channel", value=before.name, inline=False)
                embed.add_field(name="Before", value=str(before.type).replace('_', ' ').title(), inline=True)
                embed.add_field(name="After", value=str(after.type).replace('_', ' ').title(), inline=True)
                await self._send_log_embed(guild_log_channel, embed)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error in on_guild_channel_update: {e}")

async def setup(bot):
    await bot.add_cog(OnGuildChannelUpdate(bot))
