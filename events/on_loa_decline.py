import discord
from discord.ext import commands

from utils.constants import RED_COLOR


class OnLOADecline(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_loa_accept(self, loa_doc: dict):
        guild = self.bot.get_guild(loa_doc["guild_id"])
        try:
            user = await guild.fetch_member(int(loa_doc["user_id"]))
        except:
            return
        try:
            await user.send(
                embed=discord.Embed(
                    title=f"Activity Notice Declined | {guild.name}",
                    description=f"Your {loa_doc['type']} request in **{guild.name}** was declined.",
                    color=RED_COLOR,
                )
            )
        except:
            pass


async def setup(bot):
    await bot.add_cog(OnLOADecline(bot))