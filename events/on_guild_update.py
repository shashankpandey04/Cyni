import discord
from discord.ext import commands
from utils.constants import RED_COLOR, YELLOW_COLOR
from utils.utils import discord_time
import datetime
import asyncio
from cyni import premium_check_fun

class OnGuildUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_audit_log_entry(self, guild, action=discord.AuditLogAction.guild_update):
        """Get the latest audit log entry for guild updates."""
        try:
            async for entry in guild.audit_logs(action=action, limit=1):
                return entry
        except (discord.Forbidden, discord.HTTPException):
            return None

    async def _send_log_embed(self, channel, embed):
        """Send embed to log channel with error handling."""
        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"Failed to send vanity protection log: {e}")

    async def _create_base_embed(self, title, user, guild, created_at, color=YELLOW_COLOR):
        """Create a base embed with common fields."""
        user_mention = user.mention if user else "Unknown User"
        embed = discord.Embed(
            title=title,
            description=f"{user_mention} attempted to modify guild settings on {created_at}",
            color=color
        )
        embed.set_footer(text=f"Guild ID: {guild.id}")
        return embed

    async def _revert_vanity_url(self, guild, original_vanity, current_vanity, audit_entry):
        """Revert vanity URL change and log the action."""
        try:
            await guild.edit(vanity_code=original_vanity, reason="CYNI AutoMod: Unauthorized vanity URL change detected")

            sett = await self.bot.settings.find_by_id(guild.id)
            if not sett:
                return
                
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled") or not moderation_module.get("audit_log"):
                return
                
            guild_log_channel = guild.get_channel(moderation_module["audit_log"])
            if not guild_log_channel:
                return

            created_at = discord_time(datetime.datetime.now())
            embed = self._create_base_embed(
                "🛡️ Vanity URL Protection Triggered", 
                audit_entry.user if audit_entry else None, 
                guild, 
                created_at, 
                RED_COLOR
            )
            
            embed.add_field(
                name="❌ Unauthorized Change Detected",
                value=f"**Attempted Change:** `{original_vanity}` → `{current_vanity}`\n**Action:** Reverted to original",
                inline=False
            )
            
            embed.add_field(
                name="👤 User",
                value=audit_entry.user.mention if audit_entry and audit_entry.user else "Unknown",
                inline=True
            )
            
            embed.add_field(
                name="🔒 Protection Status",
                value="✅ Successfully Reverted",
                inline=True
            )
            
            if audit_entry and audit_entry.user != guild.owner:
                embed.add_field(
                    name="⚠️ Security Alert",
                    value="Non-owner attempted to change vanity URL",
                    inline=False
                )

            await self._send_log_embed(guild_log_channel, embed)
            
            try:
                owner_embed = discord.Embed(
                    title="🚨 Vanity URL Protection Alert",
                    description=f"Someone attempted to change the vanity URL in **{guild.name}**",
                    color=RED_COLOR
                )
                owner_embed.add_field(
                    name="Details",
                    value=f"**User:** {audit_entry.user.mention if audit_entry and audit_entry.user else 'Unknown'}\n**Attempted Change:** `{original_vanity}` → `{current_vanity}`\n**Status:** Automatically reverted",
                    inline=False
                )
                owner_embed.add_field(
                    name="Action Required",
                    value="Review your server permissions and consider restricting vanity URL management to trusted members only.",
                    inline=False
                )
                await guild.owner.send(embed=owner_embed)
            except (discord.Forbidden, discord.HTTPException, AttributeError):
                pass
                
        except discord.Forbidden:
            sett = await self.bot.settings.find_by_id(guild.id)
            if sett:
                moderation_module = sett.get("moderation_module", {})
                if moderation_module.get("enabled") and moderation_module.get("audit_log"):
                    guild_log_channel = guild.get_channel(moderation_module["audit_log"])
                    if guild_log_channel:
                        error_embed = discord.Embed(
                            title="❌ Vanity Protection Failed",
                            description="Bot lacks permission to revert vanity URL change",
                            color=RED_COLOR
                        )
                        error_embed.add_field(
                            name="Required Permission",
                            value="**Manage Guild** permission needed for vanity URL protection",
                            inline=False
                        )
                        await self._send_log_embed(guild_log_channel, error_embed)
        except Exception as e:
            print(f"Error reverting vanity URL in {guild.name} ({guild.id}): {e}")

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """
        This event is triggered when a guild is updated.
        Handles vanity URL protection and other guild setting changes.
        """
        try:
            guild = after

            sett = await self.bot.settings.find_by_id(guild.id)
            if not sett:
                return
            premium_status = await premium_check_fun(self.bot, guild)
            if premium_status in ["not_premium_server"]:
                return
            automod_module = sett.get("automod_module", {})
            vanity_protection = automod_module.get("vanity_protection", {})
            
            if vanity_protection.get("enabled", False):
                if before.vanity_url_code != after.vanity_url_code:
                    audit_entry = await self._get_audit_log_entry(guild)
                    
                    if audit_entry and audit_entry.user != guild.owner:
                        exempt_roles = vanity_protection.get("exempt_roles", [])
                        exempt_users = vanity_protection.get("exempt_users", [])
                        
                        user_is_exempt = (
                            audit_entry.user.id in exempt_users or
                            any(role.id in exempt_roles for role in audit_entry.user.roles)
                        )
                        
                        if not user_is_exempt:
                            await asyncio.sleep(1)
                            
                            await self._revert_vanity_url(
                                guild, 
                                before.vanity_url_code, 
                                after.vanity_url_code, 
                                audit_entry
                            )
                            return
            
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled") or not moderation_module.get("audit_log"):
                return
                
            guild_log_channel = guild.get_channel(moderation_module["audit_log"])
            if not guild_log_channel:
                guild_log_channel = self.bot.get_channel(moderation_module["audit_log"])
            if not guild_log_channel:
                return

            audit_entry = await self._get_audit_log_entry(guild)
            created_at = discord_time(datetime.datetime.now())

            if before.name != after.name:
                embed = await self._create_base_embed("Guild Name Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(name="Before", value=before.name, inline=True)
                embed.add_field(name="After", value=after.name, inline=True)
                await self._send_log_embed(guild_log_channel, embed)

            if before.icon != after.icon:
                embed = await self._create_base_embed("Guild Icon Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(
                    name="Change",
                    value="Guild icon has been updated",
                    inline=False
                )
                if after.icon:
                    embed.set_image(url=after.icon.url)
                await self._send_log_embed(guild_log_channel, embed)

            if before.banner != after.banner:
                embed = await self._create_base_embed("Guild Banner Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(
                    name="Change",
                    value="Guild banner has been updated",
                    inline=False
                )
                if after.banner:
                    embed.set_image(url=after.banner.url)
                await self._send_log_embed(guild_log_channel, embed)

            if before.vanity_url_code != after.vanity_url_code:
                embed = await self._create_base_embed("Vanity URL Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(
                    name="Before", 
                    value=before.vanity_url_code or "None", 
                    inline=True
                )
                embed.add_field(
                    name="After", 
                    value=after.vanity_url_code or "None", 
                    inline=True
                )
                await self._send_log_embed(guild_log_channel, embed)

            if before.verification_level != after.verification_level:
                embed = await self._create_base_embed("Verification Level Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(
                    name="Before", 
                    value=str(before.verification_level).replace('_', ' ').title(), 
                    inline=True
                )
                embed.add_field(
                    name="After", 
                    value=str(after.verification_level).replace('_', ' ').title(), 
                    inline=True
                )
                await self._send_log_embed(guild_log_channel, embed)

            if before.default_notifications != after.default_notifications:
                embed = await self._create_base_embed("Default Notifications Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(
                    name="Before", 
                    value=str(before.default_notifications).replace('_', ' ').title(), 
                    inline=True
                )
                embed.add_field(
                    name="After", 
                    value=str(after.default_notifications).replace('_', ' ').title(), 
                    inline=True
                )
                await self._send_log_embed(guild_log_channel, embed)

            if before.explicit_content_filter != after.explicit_content_filter:
                embed = await self._create_base_embed("Content Filter Updated", audit_entry.user if audit_entry else None, after, created_at)
                embed.add_field(
                    name="Before", 
                    value=str(before.explicit_content_filter).replace('_', ' ').title(), 
                    inline=True
                )
                embed.add_field(
                    name="After", 
                    value=str(after.explicit_content_filter).replace('_', ' ').title(), 
                    inline=True
                )
                await self._send_log_embed(guild_log_channel, embed)

        except Exception as e:
            print(f"Error in on_guild_update: {e}")

async def setup(bot):
    await bot.add_cog(OnGuildUpdate(bot))
