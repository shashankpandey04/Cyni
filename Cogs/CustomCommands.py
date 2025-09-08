import discord
from discord.ext import commands

from discord import app_commands
from utils.constants import RED_COLOR, BLANK_COLOR, GREEN_COLOR
from utils.utils import log_command_usage
from Views.CustomCommands import CustomCommandManager
from cyni import premium_check, is_management

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="command",
        extras={
            "category": "Custom Commands"
        }
    )
    async def command(self, ctx):
        pass

    @command.command(
        name="manage",
        extras={
            "category": "Custom Commands"
        }
    )
    @commands.guild_only()
    @premium_check()
    @is_management()
    async def manage(self, ctx):
        """
        Manage your custom commands.
        """
        try:
            if isinstance(ctx,commands.Context):
                await log_command_usage(self.bot,ctx.guild,ctx.author,"Custom Command Manage")
            if not ctx.guild:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Error",
                        description="This command can only be used in a server.",
                        color=RED_COLOR
                    )
                )
            view = CustomCommandManager(self.bot, ctx)
            embed=discord.Embed(
                    title="Custom Command Management",
                    description=" ",
                    color=BLANK_COLOR
                )
            doc = await self.bot.custom_commands.find_by_id(ctx.guild.id)
            if not doc:
                embed.description = "> No custom commands found."
            else:
                for key in doc:
                    if key != "_id":
                        command = doc[key]
                        embed.add_field(
                            name=f"Command: `{key}`",
                            value=f"> Created By: <@{command['created_by']}>\n> Created At: <t:{command['created_at']}:f>",
                            inline=False
                        )

            await ctx.send(
                embed=embed,
                view=view
            )
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred: ```{e}```",
                    color=RED_COLOR
                )
            )

async def setup(bot):
    await bot.add_cog(CustomCommands(bot))