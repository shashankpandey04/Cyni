import discord
from discord.ext import commands

from integrations.erlc.exceptions import ERLCAPIError


class ERLC(commands.Cog):
    """
    Roblox: Emergency Liberty County Response
    Server Management Commands
    """

    def __init__(self, bot):
        self.bot = bot

    def _base_erlc_embed(
        self, ctx: commands.Context, title: str, descrption: str
    ) -> discord.Embed:
        """
        Returns base ERLC Embed.
        Helps maintain consistent embed design accross all ERLC commands.
        """
        return (
            discord.Embed(title=title, description=descrption)
            .set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
            .set_footer(text="CYNI | Emergency Response Liberty County")
        )

    def _error_embed(self, error: ERLCAPIError):
        return discord.Embed(
            title="ERLC Error",
            description=error.message,
            color=discord.Color.red(),
        ).add_field(
            name="Error Code",
            value=f"`{error.code}`",
        )

    @commands.hybrid_group(name="erlc", extras={"category": "ERLC"})
    async def erlc(self, ctx):
        pass

    @erlc.command(name="status", description="Shows the current ERLC server status.")
    async def status(self, ctx: commands.Context):
        await ctx.defer()

        try:
            server = await self.bot.erlc.server(ctx.guild.id)

        except ERLCAPIError as e:
            return await ctx.reply(embed=self._error_embed(e))

        description = (
            f"> **Name:** {server.Name}\n"
            f"> **Players:** {server.CurrentPlayers}/{server.MaxPlayers}\n"
            f"> **Join Key:** `{server.JoinKey}`\n"
            f"> **Owner ID:** `{server.OwnerId}`\n"
            f"> **Team Balance:** {'Enabled' if server.TeamBalance else 'Disabled'}"
        )

        embed = self._base_erlc_embed(
            ctx,
            "Server Status",
            description,
        ).set_thumbnail(url=ctx.guild.icon)
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(ERLC(bot))
