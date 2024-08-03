import discord
from discord.ext import commands

from utils.constants import RED_COLOR, GREEN_COLOR
from utils.utils import discord_time
import datetime

class OnGuildChannelCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """
        This event is triggered when a channel is created in a guild.
        :param channel (discord.TextChannel): The channel that was created.
        """
        
        sett = await self.bot.settings.find_by_id(channel.guild.id)
        guild = channel.guild
        if not sett:
            return
        try:
            if not sett["moderation_module"]["enabled"]:
                return
        except KeyError:
            return
        try:
            if not sett["moderation_module"]["enabled"]:
                return
        except KeyError:
            return
        try:
            if not sett["moderation_module"]["audit_log"]:
                return
        except KeyError:
            return
        guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])
        created_at = discord_time(datetime.datetime.now())
        await guild_log_channel.send(
            embed = discord.Embed(
                title= " ",
                description=f"{channel.mention} was created on {created_at}",
                color=GREEN_COLOR
            ).add_field(
                name="Channel Type",
                value=f"{channel.type}",
            ).add_field(
                name="Channel Category",
                value=f"{channel.category}",
            ).set_footer(
                text=f"Channel ID: {channel.id}"
            )
        )

async def setup(bot):
    await bot.add_cog(OnGuildChannelCreate(bot))