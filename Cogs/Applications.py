import discord
from discord.ext import commands

from discord import app_commands
from cyni import is_management
from utils.autocompletes import application_autocomplete
from utils.constants import RED_COLOR, BLANK_COLOR, GREEN_COLOR
from utils.utils import log_command_usage

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="application",
        aliases=["app"],
        extras={
            "category": "Applications"
        }
    )
    async def application(self, ctx):
        pass

    @application.command(
        name="result",
        extras={
            "category": "Applications"
        }
    )
    @is_management()
    @app_commands.autocomplete(
        status = application_autocomplete
    )
    async def resut(self, ctx, applicant: discord.Member,status:str,*,feedback: str = None,role_add:discord.Role = None,role_remove:discord.Role = None):
        """
        Send the result of an application.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Application Result for {applicant}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if settings is None:
            return await ctx.send(
                embed = discord.Embed(
                    title="Error",
                    description="No settings found for this server. Please use `/config` command."
                )
            )
        try:
            application_channel_id = settings["server_management"]["application_channel"]
            application_channel = ctx.guild.get_channel(application_channel_id)
        except KeyError:
            return await ctx.send(
                embed = discord.Embed(
                    title="Error",
                    description="No application channel found. Please use `/config` command.",
                    color=0x2F3136
                )
            )
        if status == "accepted":
            embed = discord.Embed(
                title=f"Reviewed by {ctx.author}",
                description="**<:checked:1268849964063391788> Application accepted.**",
                color=GREEN_COLOR
            )
        else:
            embed = discord.Embed(
                title=f"Reviewed by {ctx.author}",
                description="**<:declined:1268849944455024671> Application declined.**",
                color=RED_COLOR
            )
        embed.add_field(
            name="Applicant",
            value=applicant.mention,
            inline=False
        ).add_field(
            name="Feedback",
            value=feedback,
            inline=False
        ).set_thumbnail(
            url=applicant.avatar.url
        )
        try:
            role_add = ctx.guild.get_role(role_add)
            role_remove = ctx.guild.get_role(role_remove)
            await applicant.add_roles(role_add)
            await applicant.remove_roles(role_remove)
        except:
            pass
        await application_channel.send(
            applicant.mention,
            embed=embed
        )
        await ctx.send(
            f"Application result sent for {applicant.mention}"
        )

async def setup(bot):
    await bot.add_cog(Applications(bot))
