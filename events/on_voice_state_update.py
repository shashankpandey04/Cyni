import discord
import time
from discord.ext import commands

from utils.constants import RED_COLOR, GREEN_COLOR, YELLOW_COLOR
from utils.utils import discord_time, generate_embed
from cyni import premium_check_fun
import datetime

class OnVoiceStateUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        This event is triggered when a member's voice state is updated.
        :param member (discord.Member): The member whose voice state was updated.
        :param before (discord.VoiceState): The member's voice state before the update.
        :param after (discord.VoiceState): The member's voice state after the update.
        """
        
        sett = await self.bot.settings.find_by_id(member.guild.id)
        guild = member.guild
        if not sett:
            return
        premium_status = await premium_check_fun(self.bot, guild)
        if premium_status in [True] and self.bot.is_premium == False:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
                return
        if sett.get("moderation_module", {}).get("audit_log") is None:
            return
        guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])
        if not guild_log_channel:
            return
        logger = self.bot.get_cog("ThrottledLogger")
        action_time = discord_time(datetime.datetime.now())
        if before.channel is None and after.channel is not None:
            embed = generate_embed(
                guild=guild,
                title="Voice Channel Joined",
                description=f"{member.mention} joined voice channel {after.channel.mention} on {action_time}",
                category="logging",
                footer=f"User ID: {member.id}",
                fields=[
                    {"name": "Channel", "value": after.channel.name, "inline": True},
                    {"name": "Joined At", "value": action_time, "inline": True}
                ]
            )
            await logger.log_embed(guild_log_channel, embed)

        elif before.channel is not None and after.channel is None:
            embed = generate_embed(
                guild=guild,
                title="Voice Channel Left",
                description=f"{member.mention} left voice channel {before.channel.mention} on {action_time}",
                category="logging",
                footer=f"User ID: {member.id}",
                fields=[
                    {"name": "Channel", "value": before.channel.name, "inline": True},
                    {"name": "Left At", "value": action_time, "inline": True}
                ]
            )
            await logger.log_embed(guild_log_channel, embed)

async def setup(bot):
    await bot.add_cog(OnVoiceStateUpdate(bot))