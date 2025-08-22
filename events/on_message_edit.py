import discord
import datetime
from discord.ext import commands

from dashboard import guild
from utils.constants import YELLOW_COLOR
from utils.utils import discord_time, generate_embed
from cyni import premium_check_fun


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
        if (before.author.bot or 
            before.content == after.content or 
            not before.guild):
            return

        try:
            sett = await self.bot.settings.find_by_id(before.guild.id)
            if not sett:
                return
            premium_status = await premium_check_fun(self.bot, before.guild)
            if premium_status in [True] and self.bot.is_premium == False:
                return
                
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled", False):
                return
                
            audit_log_id = moderation_module.get("audit_log")
            if not audit_log_id:
                return
            
            guild_log_channel = before.guild.get_channel(audit_log_id)
            if not guild_log_channel or not guild_log_channel.permissions_for(before.guild.me).send_messages:
                return
                
            before_content = before.content[:1021] + "..." if len(before.content) > 1024 else before.content
            after_content = after.content[:1021] + "..." if len(after.content) > 1024 else after.content
            
            created_at = discord_time(datetime.datetime.now())
            embed = generate_embed(
                before.guild,
                title="Message Edited",
                category="logging",
                description=f"Message by {before.author.mention} edited {created_at}",
                footer=f"Message ID: {before.id} | User ID: {before.author.id}",
                fields=[
                    {"name": "Before", "value": before_content or "(empty)", "inline": False},
                    {"name": "After", "value": after_content or "(empty)", "inline": False},
                    {"name": "Jump to Message", "value": f"[Click Here]({after.jump_url})", "inline": False},
                    {"name": "Channel", "value": before.channel.mention, "inline": True}
                ]
            )

            logger = self.bot.get_cog("ThrottledLogger")
            await logger.log_embed(guild_log_channel, embed)

        except Exception as e:
            print(f"Error in on_message_edit event: {str(e)}")

async def setup(bot):
    await bot.add_cog(OnMessageEdit(bot))