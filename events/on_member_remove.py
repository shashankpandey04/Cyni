import discord
from discord.ext import commands

from utils.constants import RED_COLOR
from utils.utils import discord_time, generate_embed
import datetime
from cyni import premium_check_fun

class OnMemberRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """
        This event is triggered when a member leaves a guild.
        :param member (discord.Member): The member that left the guild.
        """
        sett = await self.bot.settings.find_by_id(member.guild.id)
        guild = member.guild
        premium_status = await premium_check_fun(self.bot, guild)
        if premium_status in ["use_premium_bot", "use_regular_bot"]:
            return
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
            return
        guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])
        if not guild_log_channel:
            return

        left_at = discord_time(datetime.datetime.now())

        embed = await generate_embed(
            guild,
            title="Member Left",
            category="logging",
            description=f"{member.mention} left the server on {left_at}",
            footer=f"User ID: {member.id}",
            fields=[
                {"name": "Member Count", "value": f"{guild.member_count}", "inline": True},
                {"name": "Username", "value": f"{member.name}#{member.discriminator}", "inline": True}
            ]
        )
        await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnMemberRemove(bot))