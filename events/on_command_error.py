import datetime
import os
import traceback
import logging
from utils.utils import gen_error_uid
from cyni import PremiumRequired

import discord
from discord.ext import commands

from utils.utils import gen_error_uid
from dotenv import load_dotenv

from utils.prc_api import ResponseFailed
from utils.constants import BLANK_COLOR

load_dotenv()

class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command."""
        
        # Get the original exception
        error = getattr(error, 'original', error)
        
        if hasattr(ctx.command, 'on_error'):
            return
        
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, PremiumRequired):
            return await ctx.send(
                embed=discord.Embed(
                    title="Premium Required",
                    description=str(error),
                    color=discord.Color.red()
                )
            )

        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You are missing a required argument.",
                    color=discord.Color.red()
                )
            )
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"You don't have the required permissions to use this command: {error}")
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="I am missing the required permissions.",
                    color=discord.Color.red()
                )
            )
        
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"This command is on cooldown. Try again in {error.retry_after:.2f}s.",
                    color=discord.Color.red()
                )
            )
        
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You do not have permission to run this command.",
                    color=discord.Color.red()
                )
            )

        if isinstance(error, ResponseFailed):
            return await ctx.reply(
                embed=discord.Embed(
                    title=f"PRC Response Failure ({error.code})",
                    description="Your server seems to be offline. If this is incorrect, PRC's API may be down." if error.code == 422 else "There seems to be issues with the PRC API. Stand by and wait a few minutes before trying again.",
                    color=BLANK_COLOR
                )
            )
        
        if isinstance(error, commands.CommandInvokeError):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="An error occurred.",
                    color=discord.Color.red()
                )
            )
        
        if isinstance(error, commands.MaxConcurrencyReached):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="This command is already running.",
                    color=discord.Color.red()
                )
            )

        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="This command cannot be used in private messages.",
                    color=discord.Color.red()
                )
            )
        
        if isinstance(error, commands.DisabledCommand):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="This command is disabled.",
                    color=discord.Color.red()
                )
            )
        
        # AutoShardedConnectionState error handling
        if "'AutoShardedConnectionState' object has no attribute '_interaction'" in str(error):
            try:
                await ctx.send("There was an issue processing this command as a hybrid command. Try using the regular command prefix.")
            except:
                pass
            return
            
        # Log all other errors
        error_message = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        logging.error(f"Command {ctx.command} error: {error_message}")
        
        # Notify the user
        await ctx.send(f"An error occurred: {str(error)}")

async def setup(bot):
    await bot.add_cog(CommandErrorHandler(bot))
