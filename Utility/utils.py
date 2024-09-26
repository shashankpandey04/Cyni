from discord.ext import commands

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
