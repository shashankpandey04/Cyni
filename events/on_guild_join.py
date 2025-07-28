import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

from utils.constants import BLANK_COLOR
from utils.utils import discord_time, generate_embed

class OnGuildJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_log_channel = None

    async def cog_load(self):
        log_guild = self.bot.get_guild(1152949579407442050)
        if log_guild:
            self.guild_log_channel = log_guild.get_channel(1210248878599839774)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """
        This event is triggered when the bot joins a guild.
        :param guild (discord.Guild): The guild that the bot joined.
        """

        if self.bot.is_premium:
            premium = await self.bot.premium.find_by_id(guild.id)
            if not premium:
                embed = discord.Embed(
                    title="⚠️ Your server is not premium!",
                    description="Please upgrade to premium to use this bot.",
                    color=discord.Color.red()
                )
                embed.set_footer(text="CYNI Premium")
                await guild.owner.send(embed=embed)
                await guild.leave()
                return
        
        if not self.guild_log_channel:
            log_guild = self.bot.get_guild(1152949579407442050)
            if log_guild:
                self.guild_log_channel = log_guild.get_channel(1210248878599839774)
        if not self.guild_log_channel:
            return
        
        created_at = discord_time(guild.created_at)
        embed = generate_embed(
            guild,
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
            footer=f"Guild ID: {guild.id}",
        )
        try:
            embed.set_thumbnail(url=guild.icon_url)
        except:
            pass
        await self.guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnGuildJoin(bot))
