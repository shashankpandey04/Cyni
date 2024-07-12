import discord
from discord.ext import commands

from cyni import is_management

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
        name="accept",
        extras={
            "category": "Applications"
        }
    )
    @is_management()
    async def accept(self, ctx, applicant: discord.Member,*,feedback: str = None,role_add:discord.Role = None,role_remove:discord.Role = None):
        """
        Accept an application.
        """
        try:
            settings = await self.bot.settings.find_by_id(ctx.guild.id)
            if settings is None:
                return await ctx.send(
                    embed = discord.Embed(
                        title="Error",
                        description="No settings found for this server. Please use `/config` command."
                    )
                )
            try:
                application_channel_id = settings["logging_channels"]["application_channel"]
                application_channel = ctx.guild.get_channel(application_channel_id)
            except KeyError:
                return await ctx.send(
                    embed = discord.Embed(
                        title="Error",
                        description="No application channel found. Please use `/config` command.",
                        color=0x2F3136
                    )
                )
            embed = discord.Embed(
                title=f"Reviewd by {ctx.author}",
                description="**✅ Application accepted.**",
                color=discord.Color.brand_green()
            ).add_field(
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
                f"Application accepted for {applicant.mention}."
            )
        except Exception as e:
            await ctx.send(
                embed = discord.Embed(
                    title="Error",
                    description=f"An error occured: {e}",
                    color=0x2F3136
                )
            )

    @application.command(
        name="reject",
        extras={
            "category": "Applications"
        }
    )
    @is_management()
    async def reject(self, ctx, applicant: discord.Member,*,feedback: str = None):
        """
        Reject an application.
        """
        try:
            settings = await self.bot.settings.find_by_id(ctx.guild.id)
            if settings is None:
                return await ctx.send(
                    embed = discord.Embed(
                        title="Error",
                        description="No settings found for this server. Please use `/config` command."
                    )
                )
            try:
                application_channel = settings["logging_channels"]["application_channel"]
                application_channel = ctx.guild.get_channel(application_channel)
            except KeyError:
                return await ctx.send(
                    embed = discord.Embed(
                        title="Error",
                        description="No application channel found. Please use `/config` command.",
                        color=0x2F3136
                    )
                )
            embed = discord.Embed(
                title=f"Reviewd by {ctx.author}",
                description="**❌ Application rejected.**",
                color=discord.Color.brand_red()
            ).add_field(
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
            await application_channel.send(applicant.mention,embed=embed)
            await ctx.send(
                f"Application rejected for {applicant.mention}."
            )
        except Exception as e:
            await ctx.send(
                embed = discord.Embed(
                    title="Error",
                    description=f"An error occured: {e}",
                    color=0x2F3136
                )
            )

async def setup(bot):
    await bot.add_cog(Applications(bot))
