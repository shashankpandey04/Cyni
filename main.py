import asyncio
import discord
from discord.ext import commands
from tokens import get_token
from utils import create_or_get_server_config, cleanup_guild_data
import os

# Importing bot instance from cyni.py
from cyni import bot

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

async def main():
    TOKEN = get_token()
    directories = ['Cogs', 'Roblox', 'ImagesCommand', 'Staff_Commands']
    
    await load_all_extensions(bot, directories)
    await bot.tree.sync()
    bot.start_time = time.time()
    for guild in bot.guilds:
        create_or_get_server_config(guild.id)
    cleanup_guild_data(bot)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/support | Cyni"))
    await bot.load_extension("jishaku")
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print(f'Version: {discord.__version__}')
    print('------')

if __name__ == '__main__':
    asyncio.run(main())
    bot.run(get_token())
