import discord
from discord.ext import commands

from utils.pagination import Pagination
from cyni import is_management, premium_check
from utils.constants import BLANK_COLOR, RED_COLOR
from utils.utils import log_command_usage

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="premium",
        aliases=["aff"],
    )
    @commands.guild_only()
    async def premium(self, ctx: commands.Context):
        """
        Get the premium link for the bot.
        """
        is_premium = await self.bot.premium(ctx.guild.id)
        embed = discord.Embed(
            title="CYNI Premium Server",
            description=(
                f"Premium Perks:\n"
                "- **Custom Commands**: Create your own commands for the server.\n"
                "- **Custom Prefix**: Set a custom prefix for the bot in your server.\n"
                "- **Application Banners**: Upload custom banners for your applications.\n"
                "- **Added Ticket Categories**: Upto 5 different ticket categories.\n"
                "- **Added Recurring Messages**: Upto 25 recurring messages.\n"
                "- **Auto Responders**: Set up auto responders for your server.\n"
            ),
            color=BLANK_COLOR
        )
        if is_premium:
            embed.add_field(
                name="Premium Status",
                value="This server is a premium server.",
                inline=False
            )
        else:
            embed.add_field(
                name="Premium Status",
                value="This server is not a premium server.",
                inline=False
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Misc(bot))