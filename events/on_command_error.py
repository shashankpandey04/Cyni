import datetime
import os
import traceback
from utils.utils import gen_error_uid
from cyni import PremiumRequired

import discord
from discord.ext import commands

from utils.utils import gen_error_uid
from dotenv import load_dotenv

from utils.prc_api import ResponseFailed
from utils.constants import BLANK_COLOR

load_dotenv()

class OnCommandError(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_command_error")
    async def on_command_error(self, ctx, error):
        
        error_id = gen_error_uid()
        
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
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You are missing the required permissions.",
                    color=discord.Color.red()
                )
            )
        
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
        
        await self.bot.errors_document.insert_one({
            "_id": error_id,
            "error": str(error),
            "traceback": traceback.format_exc(),
            "time": datetime.datetime.now() + datetime.timedelta(hours=5, minutes=30),
        })
        return await ctx.send(
            embed=discord.Embed(
                title="An Error Occured",
                description=f"An error occurred. Please report this error to the Support Team.\n\nError ID: `{error_id}`",
                color=discord.Color.red()
            )
        )

async def setup(bot):
    await bot.add_cog(OnCommandError(bot))
        