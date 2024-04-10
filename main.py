import asyncio
import discord
from discord.ext import commands
from tokens import get_token
from utils import create_or_get_server_config, cleanup_guild_data
import os
import time
from cyni import bot  # Importing bot instance from cyni.py

async def load_extensions_from_directory(bot, directory):
    """Load extensions (Cogs) from a specified directory."""
    for filename in os.listdir(directory):
        if filename.endswith('.py'):
            try:
                module_name = f'{os.path.basename(directory)}.{filename[:-3]}'
                await bot.load_extension(module_name)
                print(f'Loaded {module_name}')
            except Exception as e:
                print(f'Failed to load extension {module_name}: {e}')

async def load_all_extensions(bot, directories):
    """Load all extensions from specified directories."""
    for directory in directories:
        await load_extensions_from_directory(bot, directory)

async def setup_bot():
    try:
        directories = ['Cogs', 'Roblox', 'ImagesCommand', 'Staff_Commands']
        await load_all_extensions(bot, directories)
        bot.start_time = time.time()
        for guild in bot.guilds:
            create_or_get_server_config(guild.id)
        cleanup_guild_data(bot)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/support | Cyni"))
        await bot.load_extension("jishaku")
        print(f'Logged in as {bot.user.name} - {bot.user.id}')
        print(f'Version: {discord.__version__}')
        print('------')
        await bot.tree.sync(application_id=1136945734399295538)
    except Exception as e:
        print(f'An error occurred during startup: {e}')

if __name__ == '__main__':
    TOKEN = get_token()
    asyncio.run(setup_bot())
    bot.run(TOKEN)