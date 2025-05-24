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
from utils.constants import BLANK_COLOR, RED_COLOR

load_dotenv()

class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('bot.commands')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command."""
        
        # Early returns for special cases
        if hasattr(ctx.command, 'on_error') or isinstance(error, commands.CommandNotFound):
            return
        
        # Get the original exception
        error = getattr(error, 'original', error)
        
        # Create standard error embed template
        embed = discord.Embed(title="Error", color=RED_COLOR)
        
        # Handle different error types
        try:
            if isinstance(error, PremiumRequired):
                embed.title = "Premium Required"
                embed.description = str(error)
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
            
            # Catch-all for other CommandInvokeErrors
            elif isinstance(error, commands.CommandInvokeError):
                error_id = f"ERR-{ctx.command.name}-{ctx.author.id}-{ctx.message.id}"
                embed.description = f"An unexpected error occurred. Error ID: `{error_id}`"
                
                # Log the full error
                error_message = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
                self.logger.error(f"Command {ctx.command} error ID {error_id}: {error_message}")
                
                # Log to error channel if configured
                if hasattr(self.bot, 'error_channel_id') and self.bot.error_channel_id:
                    try:
                        error_channel = self.bot.get_channel(self.bot.error_channel_id)
                        if error_channel:
                            error_embed = discord.Embed(
                                title=f"Error ID: {error_id}",
                                description=f"```py\n{error_message[:4000]}```",
                                color=discord.Color.red()
                            )
                            error_embed.add_field(name="Command", value=ctx.command.qualified_name)
                            error_embed.add_field(name="Author", value=f"{ctx.author} ({ctx.author.id})")
                            error_embed.add_field(name="Channel", value=f"{ctx.channel} ({ctx.channel.id})")
                            if ctx.guild:
                                error_embed.add_field(name="Guild", value=f"{ctx.guild.name} ({ctx.guild.id})")
                            await error_channel.send(embed=error_embed)
                    except Exception as e:
                        self.logger.error(f"Failed to log error to error channel: {e}")
                
            else:
                # Unhandled error type
                error_message = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
                self.logger.error(f"Unhandled command error in {ctx.command}: {error_message}")
                embed.description = f"An unknown error occurred: {str(error)[:1000]}"
            
            # Send the error message to the user
            await ctx.send(embed=embed)
            
        except Exception as e:
            # Error in the error handler itself
            self.logger.error(f"Error in the error handler: {str(e)}")
            try:
                await ctx.send("An error occurred while processing your command.")
            except:
                pass

async def setup(bot):
    await bot.add_cog(CommandErrorHandler(bot))
