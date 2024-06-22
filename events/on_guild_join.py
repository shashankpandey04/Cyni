import discord
from discord.ext import commands

from utils.Schema import server_settings

class OnGuildJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild,bot):

        """
        This event is triggered when the bot joins a guild.
        :param guild (discord.Guild): The guild that the bot joined.
        :param bot (commands.Bot): The bot instance.
        """
        
        log_guild = bot.get_guild(1152949579407442050)
        guild_log_channel = log_guild.get_channel(1210248878599839774)

        await guild_log_channel.send(
            embed = discord.Embed(
                title=f"Joined {guild.name}",
                description=f"""
                > **Owner:** {guild.owner}
                > **Members:** {guild.member_count}
                > **ID:** {guild.id}
                > **Bot Count:** {len([member for member in guild.members if member.bot])}
                > **User Count:** {len([member for member in guild.members if not member.bot])}
                > **Created At:** {guild.created_at}
                > **Verification Level:** {guild.verification_level}
                """,
            )
        )

async def setup(bot):
    await bot.add_cog(OnGuildJoin(bot))