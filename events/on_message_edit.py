import discord
import datetime
from discord.ext import commands

from utils.constants import YELLOW_COLOR
from utils.utils import discord_time


class OnMessageEdit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """
        This event is triggered when a message is edited.
        
        Parameters:
        -----------
        before: discord.Message
            The message before it was edited.
        after: discord.Message
            The message after it was edited.
        """
        # Skip if conditions are not met for logging
        if (before.author.bot or 
            before.content == after.content or 
            not before.guild):  # Added check for DM messages
            return
            
        # Get settings
        try:
            sett = await self.bot.settings.find_by_id(before.guild.id)
            if not sett:
                return
                
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled", False):
                return
                
            audit_log_id = moderation_module.get("audit_log")
            if not audit_log_id:
                return
                
            # Get channel and verify permissions
            guild_log_channel = before.guild.get_channel(audit_log_id)
            if not guild_log_channel or not guild_log_channel.permissions_for(before.guild.me).send_messages:
                return
                
            # Format content for embedding
            before_content = before.content[:1021] + "..." if len(before.content) > 1024 else before.content
            after_content = after.content[:1021] + "..." if len(after.content) > 1024 else after.content
            
            # Create timestamp
            created_at = discord_time(datetime.datetime.now())
            
            # Build embed
            embed = discord.Embed(
                title="Message Edited",
                description=f"Message by {before.author.mention} edited {created_at} in {before.channel.mention}",
                color=YELLOW_COLOR
            )
            
            embed.add_field(name="Before", value=before_content or "(empty)", inline=False)
            embed.add_field(name="After", value=after_content or "(empty)", inline=False)
            embed.set_footer(text=f"Message ID: {before.id} | User ID: {before.author.id}")
            
            # Add jump URL
            embed.add_field(name="Jump to Message", value=f"[Click Here]({after.jump_url})", inline=False)
            
            # Send log
            await guild_log_channel.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error in on_message_edit event: {str(e)}")

async def setup(bot):
    await bot.add_cog(OnMessageEdit(bot))