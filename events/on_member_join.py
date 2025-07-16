import discord
import time
from discord.ext import commands
from utils.constants import GREEN_COLOR
from utils.utils import discord_time
import datetime

class OnMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

            # Handle audit logging
            await self._handle_audit_log(member, guild, sett)
            
            # Handle welcome message
            await self._handle_welcome_message(member, guild, sett)
            
        except Exception as e:
            print(f"Error in on_member_join: {e}")

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