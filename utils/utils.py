import discord
from discord.ext import commands

import asyncio
import datetime
import uuid

async def get_prefix(bot, message):
    """
    Get the prefix for the bot.
    :param bot (Bot): The bot.
    :param message (discord.Message): The message.
    :return (str): The prefix.
    """
    settings = await bot.settings.get(message.guild.id)
    
    if settings is None:
        return commands.when_mentioned_or("?")(bot,message)
    try:
        customization = settings.get("customization")
        if customization is None:
            return commands.when_mentioned_or("?")(bot,message)
        prefix = customization.get("prefix")
        if prefix is None:
            return commands.when_mentioned_or("?")(bot,message)
        return prefix
    except KeyError:
        return commands.when_mentioned_or("?")(bot,message)
    
main_config_embed = discord.Embed(
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

def gen_error_uid():
    """
    Generate a unique error ID.
    :return (str): The unique error ID.
    """
    return str(uuid.uuid4().hex[:6])