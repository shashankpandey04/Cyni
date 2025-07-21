import discord
import time
from discord.ext import commands
from utils.constants import GREEN_COLOR
from utils.utils import discord_time
import datetime
import asyncio
import logging

class OnMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Raid detection tracking
        self.join_timestamps = {}  # guild_id: [timestamps]

    async def _handle_automod_raid_detection(self, member, settings):
        """Handle raid detection AutoMod."""
        automod_settings = settings.get("automod_module", {})
        raid_settings = automod_settings.get("raid_detection", {})
        
        if not automod_settings.get("enabled", False) or not raid_settings.get("enabled", False):
            return False
            
        guild_id = member.guild.id
        current_time = time.time()
        
        # Initialize guild tracking if not exists
        if guild_id not in self.join_timestamps:
            self.join_timestamps[guild_id] = []
            
        # Add current join timestamp
        self.join_timestamps[guild_id].append(current_time)
        
        # Clean old timestamps outside time window
        time_window = raid_settings.get("time_window", 10)
        self.join_timestamps[guild_id] = [
            timestamp for timestamp in self.join_timestamps[guild_id]
            if current_time - timestamp <= time_window
        ]
        
        # Check if threshold exceeded
        join_threshold = raid_settings.get("join_threshold", 5)
        if len(self.join_timestamps[guild_id]) >= join_threshold:
            action = raid_settings.get("action", "kick")
            
            try:
                # Take action on the member
                if action == "kick":
                    await member.kick(reason="AutoMod: Raid detection")
                    action_text = "kicked"
                elif action == "ban":
                    await member.ban(reason="AutoMod: Raid detection", delete_message_days=0)
                    action_text = "banned"
                else:
                    action_text = "detected"
                
                # Send alert
                embed = discord.Embed(
                    title="🚨 AutoMod: Raid Detected",
                    description=f"**Member:** {member.mention}\n**Action:** {action_text}\n**Joins in window:** {len(self.join_timestamps[guild_id])}/{join_threshold}",
                    color=0xff0000,
                    timestamp=datetime.datetime.utcnow()
                )
                embed.add_field(name="Time Window", value=f"{time_window} seconds", inline=True)
                embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
                embed.set_thumbnail(url=member.display_avatar.url)
                
                await self._send_automod_alert(member.guild, raid_settings.get("alert_channel"), embed)
                
                return True
                
            except discord.Forbidden:
                logging.warning(f"AutoMod: Insufficient permissions to handle raid member {member.id}")
            except Exception as e:
                logging.error(f"AutoMod raid detection error: {e}")
        
        return False

    async def _send_automod_alert(self, guild, alert_channel_id, embed):
        """Send AutoMod alert to specified channel."""
        if not alert_channel_id:
            return
            
        try:
            alert_channel = guild.get_channel(alert_channel_id)
            if alert_channel:
                await alert_channel.send(embed=embed)
        except Exception as e:
            logging.error(f"Error sending AutoMod alert: {e}")

    async def _send_log_embed(self, channel, embed):
        """Send an embed to the log channel with error handling."""
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error sending member join log: {e}")

    async def _send_welcome_message(self, channel, content=None, embed=None):
        """Send a welcome message with error handling."""
        try:
            if embed:
                await channel.send(embed=embed)
            elif content:
                await channel.send(content)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error sending welcome message: {e}")

    async def _add_welcome_role(self, member, role):
        """Add welcome role to member with error handling."""
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error adding welcome role: {e}")

    def _format_welcome_message(self, message, member, guild):
        """Format welcome message with placeholders."""
        replacements = {
            "{user}": member.mention,
            "{server}": guild.name,
            "{user_name}": member.name,
            "{user_discriminator}": member.discriminator,
            "{user_id}": str(member.id),
            "{server_id}": str(guild.id),
            "{member_count}": str(guild.member_count)
        }
        
        for placeholder, value in replacements.items():
            message = message.replace(placeholder, value)
        
        return message

    def _is_new_account(self, member, days=7):
        """Check if account is newer than specified days."""
        return (time.time() - member.created_at.timestamp()) < (days * 24 * 60 * 60)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        This event is triggered when a member joins a guild.
        """
        try:
            guild = member.guild
            sett = await self.bot.settings.find_by_id(guild.id)
            if not sett:
                return

            # Handle AutoMod raid detection first (may result in immediate action)
            if await self._handle_automod_raid_detection(member, sett):
                # If raid action was taken, still log the join but don't process welcome
                await self._handle_audit_log(member, guild, sett)
                return

            # Handle audit logging
            await self._handle_audit_log(member, guild, sett)
            
            # Handle welcome message
            await self._handle_welcome_message(member, guild, sett)
            
        except Exception as e:
            print(f"Error in on_member_join: {e}")
            logging.error(f"Error in on_member_join: {e}")

    async def _handle_audit_log(self, member, guild, sett):
        """Handle audit logging for member join."""
        moderation_module = sett.get("moderation_module", {})
        if not moderation_module.get("enabled", False) or not moderation_module.get("audit_log"):
            return
            
        guild_log_channel = guild.get_channel(moderation_module["audit_log"])
        if not guild_log_channel:
            return

        joined_at = discord_time(datetime.datetime.now())
        
        # Check if account is new
        if self._is_new_account(member):
            description = f"**⚠️ Account is less than 7 days old!**\n{member.mention} joined the server on {joined_at}"
        else:
            description = f"{member.mention} joined the server on {joined_at}"
        
        embed = discord.Embed(
            title="Member Joined",
            description=description,
            color=GREEN_COLOR
        ).add_field(
            name="Account Created",
            value=discord_time(member.created_at),
            inline=True
        ).add_field(
            name="Member Count",
            value=str(guild.member_count),
            inline=True
        ).set_footer(
            text=f"User ID: {member.id}"
        )
        
        # Add avatar if available
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        await self._send_log_embed(guild_log_channel, embed)

    async def _handle_welcome_message(self, member, guild, sett):
        """Handle welcome message for new member."""
        welcome_module = sett.get('welcome_module', {})
        if not welcome_module.get('enabled', False):
            return
            
        welcome_channel = guild.get_channel(welcome_module.get('welcome_channel'))
        if not welcome_channel:
            return
            
        welcome_message = welcome_module.get('welcome_message', '')
        welcome_role = guild.get_role(welcome_module.get('welcome_role'))
        use_embed = welcome_module.get('use_embed', False)
        embed_color = welcome_module.get('embed_color', '000000')
        embed_title = welcome_module.get('embed_title', 'Welcome!')

        # Format message with placeholders
        formatted_message = self._format_welcome_message(welcome_message, member, guild)
        
        # Send welcome message
        if use_embed:
            try:
                embed = discord.Embed(
                    title=embed_title,
                    description=formatted_message,
                    color=int(embed_color, 16)
                )
                if member.avatar:
                    embed.set_thumbnail(url=member.avatar)
                await self._send_welcome_message(welcome_channel, embed=embed)
            except ValueError:
                # Invalid color format, fallback to default
                embed = discord.Embed(
                    title=embed_title,
                    description=formatted_message,
                    color=GREEN_COLOR
                )
                if member.avatar:
                    embed.set_thumbnail(url=member.avatar.url)
                await self._send_welcome_message(welcome_channel, embed=embed)
        else:
            await self._send_welcome_message(welcome_channel, content=formatted_message)
        
        # Add welcome role if specified
        if welcome_role:
            await self._add_welcome_role(member, welcome_role)

async def setup(bot):
    await bot.add_cog(OnMemberJoin(bot))