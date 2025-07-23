import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

from utils.constants import BLANK_COLOR
from utils.utils import discord_time, generate_embed

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
        embed = generate_embed(
            guild.id,
            title=f"Joined {guild.name}",
            category="logging",
            description=f"""
            > **Owner:** {guild.owner}
            > **Members:** {guild.member_count}
            > **ID:** {guild.id}
            > **Bot Count:** {len([member for member in guild.members if member.bot])}
            > **User Count:** {len([member for member in guild.members if not member.bot])}
            > **Guild Count:** {len(self.bot.guilds)}
            """,
            footer=f"Created at: {created_at}"
        )
        try:
            embed.set_thumbnail(url=guild.icon_url)
        except:
            pass
        await guild_log_channel.send(
            embed=embed
        )

async def setup(bot):
    await bot.add_cog(OnGuildJoin(bot))
