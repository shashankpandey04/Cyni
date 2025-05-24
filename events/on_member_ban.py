import discord
import datetime
from discord.ext import commands

from utils.constants import RED_COLOR
from utils.utils import discord_time


class OnMemberBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """
        This event is triggered when a member is banned from a guild.
        
        Parameters:
        -----------
        guild: discord.Guild
            The guild where the member was banned.
        user: discord.User
            The user that was banned.
        """
        # Retrieve settings
        sett = await self.bot.settings.find_by_id(guild.id)
        
        # Validate settings and requirements
        if not sett:
            return
            
        moderation_module = sett.get("moderation_module", {})
        if not moderation_module.get("enabled", False):
            return
            
        audit_log_id = moderation_module.get("audit_log")
        if not audit_log_id:
            return
            
        guild_log_channel = guild.get_channel(audit_log_id)
        if not guild_log_channel:
            return
        
        # Get ban information from audit logs
        ban_entry = None
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                ban_entry = entry
                break
        except discord.errors.Forbidden:
            # Bot doesn't have permission to view audit logs
            return
            
        if not ban_entry:
            return
        
        # Build and send embed
        created_at = discord_time(datetime.datetime.now())
        
        embed = discord.Embed(
            title="Member Banned",
            description=f"{ban_entry.user.mention} banned {user.mention}\nUser was banned {created_at}",
            color=RED_COLOR
        )
        
        embed.set_footer(text=f"User ID: {user.id}")
        
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        try:
            await guild_log_channel.send(embed=embed)
        except discord.errors.Forbidden:
            # Bot doesn't have permission to send messages
            pass


async def setup(bot):
    await bot.add_cog(OnMemberBan(bot))