import discord
from discord.ext import commands

from utils.constants import BLANK_COLOR
from utils.utils import discord_time

class OnGuildJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """
        This event is triggered when the bot joins a guild.
        :param guild (discord.Guild): The guild that the bot joined.
        """
        
        log_guild = self.bot.get_guild(1152949579407442050)
        guild_log_channel = log_guild.get_channel(1210248878599839774)
        created_at = discord_time(guild.created_at)
        await guild_log_channel.send(
            embed = discord.Embed(
                title=f"Joined {guild.name}",
                description=f"""
                <:anglesmallright:1268850037861908571> **Owner:** {guild.owner}
                <:anglesmallright:1268850037861908571> **Members:** {guild.member_count}
                <:anglesmallright:1268850037861908571> **ID:** {guild.id}
                <:anglesmallright:1268850037861908571> **Bot Count:** {len([member for member in guild.members if member.bot])}
                <:anglesmallright:1268850037861908571> **User Count:** {len([member for member in guild.members if not member.bot])}
                <:anglesmallright:1268850037861908571> **Created At:** {created_at}
                <:anglesmallright:1268850037861908571> **Verification Level:** {guild.verification_level}
                <:anglesmallright:1268850037861908571> **Guild Count:** {len(self.bot.guilds)}
                """,
                color=BLANK_COLOR
            ).set_thumbnail(
                url=guild.icon.url if guild.icon else ' '
            )
        )

async def setup(bot):
    await bot.add_cog(OnGuildJoin(bot))
