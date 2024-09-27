import os
import dotenv
from discord.ext import commands

dotenv.load_dotenv()

async def get_prefix(bot, message) -> str:
    """
    Get the prefix for the bot
    :param bot (Bot): The bot instance.
    :param message (discord.Message): The message.
    :return (str): The prefix.
    """
    DATABASE = os.getenv('DATABASE')
    if DATABASE == 'MONGO':
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
    elif DATABASE == 'MYSQL':
        query = f"SELECT prefix FROM settings WHERE guild_id = {message.guild.id}"
        cursor = bot.db.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        if result is None:
            return commands.when_mentioned_or("?")(bot,message)
        return result[0]