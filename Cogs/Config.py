import discord
from discord.ext import commands
from menu import SetupBot

from cyni import is_management

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="config",
        aliases=["settings"],
        extras={
            "category": "Settings"
        }
    )
    @commands.guild_only()
    @is_management()
    async def config(self, ctx):
        """
        Configure your server settings.
        """
        try:
            embed = discord.Embed(
                title="Configuration",
                description="Configure your server settings.",
                color=discord.Color.blurple()
            ).add_field(
                name="Basic Configuration",
                value="Setup your Staff & Management Roles to use Cyni.",
                inline=False
            ).add_field(
                name="Anti-Ping",
                value="What is Anti-Ping? Anti-Ping prevents users from pinging specific roles.",
                inline=False
            ).add_field(
                name="Staff Infractions Module",
                value="Setup the Staff Infractions module to log staff infractions.",
                inline=False
            ).add_field(
                name="Log Channels",
                value="Set channels to log moderation actions and applications.",
                inline=False
            ).add_field(
                name="Other Configurations",
                value="Setup Prefix and Message Quota.",
                inline=False
            )

            await ctx.send(
                embed=embed, 
                view=SetupBot(bot=self.bot, user_id=ctx.author.id)
            )

        except discord.HTTPException:
            pass

async def setup(bot):
    await bot.add_cog(Config(bot))
