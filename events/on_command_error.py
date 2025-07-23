import datetime
import os
import traceback
import logging
from utils.utils import generate_embed
from cyni import PremiumRequired

import discord
from discord.ext import commands

from dotenv import load_dotenv

from utils.prc_api import ResponseFailed, ServerLinkNotFound
from utils.constants import BLANK_COLOR, RED_COLOR

load_dotenv()

class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('bot.commands')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command."""
        
        if hasattr(ctx.command, 'on_error') or isinstance(error, commands.CommandNotFound):
            return
        
        error = getattr(error, 'original', error)

        # Get premium status and custom colors for embed generation
        guild = ctx.guild
        if guild:
            try:
                sett = await self.bot.settings.find_by_id(guild.id)
                premium_status = sett.get("premium", False) if sett else False
                custom_colors = sett.get("customization", {}).get("embed_colors", {}) if premium_status else {}
            except:
                premium_status = False
                custom_colors = {}
        else:
            premium_status = False
            custom_colors = {}

        embed = generate_embed(
            guild, 
            title="Error", 
            category="error",
            premium=premium_status,
            custom_colors=custom_colors
        )

        try:
            if isinstance(error, PremiumRequired):
                embed.title = "Premium Required"
                embed.description = "This command requires Cyni Premium. Please upgrade your server to use this command."
                return await ctx.send(embed=embed)
                
            elif isinstance(error, commands.MissingRequiredArgument):
                embed.description = f"Missing required argument: `{error.param.name}`"
                
            elif isinstance(error, commands.MissingPermissions):
                missing = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
                embed.description = f"You're missing these permissions: {', '.join(missing)}"
                
            elif isinstance(error, commands.BotMissingPermissions):
                missing = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
                embed.description = f"I'm missing these permissions: {', '.join(missing)}"
                
            elif isinstance(error, commands.CommandOnCooldown):
                embed.description = f"This command is on cooldown. Try again in {error.retry_after:.2f}s."
                
            elif isinstance(error, ServerLinkNotFound):
                embed.title = "ERLC Server Not Linked"
                embed.description = "This Discord server is not linked to an ERLC server. Use `/erlc link` to link your server first."
                embed.color = BLANK_COLOR
                
            elif isinstance(error, commands.CheckFailure):
                embed.description = "You do not have permission to run this command."
                
            elif isinstance(error, ResponseFailed):
                embed.title = f"PRC Response Failure ({error.code})"
                embed.description = "Your server seems to be offline." if error.code == 422 else "There seems to be issues with the PRC API. Try again later."
                embed.color = BLANK_COLOR
                return await ctx.reply(embed=embed)
                
            elif isinstance(error, commands.MaxConcurrencyReached):
                embed.description = f"This command is already running. (Limit: {error.number} {error.per.name})"
                
            elif isinstance(error, commands.NoPrivateMessage):
                embed.description = "This command cannot be used in private messages."
                
            elif isinstance(error, commands.DisabledCommand):
                embed.description = "This command is disabled."
            
            # AutoShardedConnectionState error handling
            elif "'AutoShardedConnectionState' object has no attribute '_interaction'" in str(error):
                embed.description = "There was an issue processing this command as a hybrid command. Try using the regular command prefix."
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error in the error handler: {str(e)}")
            try:
                await ctx.send("An error occurred while processing your command.")
            except:
                pass

async def setup(bot):
    await bot.add_cog(CommandErrorHandler(bot))
