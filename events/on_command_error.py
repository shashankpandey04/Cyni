import datetime
import os
import traceback

import discord
from discord.ext import commands

import asyncio
from sentry_sdk import capture_exception, push_scope
from utils.utils import gen_error_uid
from dotenv import load_dotenv

load_dotenv()

class OnCommandError(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_command_error")
    async def on_command_error(self, ctx, error):
        
        if hasattr(ctx.command, "on_error"):
            return
        
        if isinstance(error, commands.CommandNotFound):
            return
        
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
        
        if isinstance(error, commands.CommandError):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="An error occurred.",
                    color=discord.Color.red()
                )
            )

        if isinstance(error, commands.BadArgument):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You provided a bad argument.",
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

async def setup(bot):
    await bot.add_cog(OnCommandError(bot))
        