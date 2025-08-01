import discord
from discord.ext import commands

from utils.pagination import Pagination
from cyni import is_management, premium_check
from utils.constants import BLANK_COLOR, RED_COLOR
from utils.utils import log_command_usage

class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="verify",
        aliases=["verification"],
        description="Verify a user in the server."
    )
    @commands.guild_only()
    @premium_check()
    async def verify(self, ctx: commands.Context):
        """
        Verify a user in the server.
        """
        await ctx.send(f"Verifying {ctx.author.mention}...")

        if not ctx.author or not hasattr(ctx.author, 'id'):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Unable to identify the command user.",
                    color=RED_COLOR
                )
            )


async def setup(bot):
    await bot.add_cog(Verify(bot))