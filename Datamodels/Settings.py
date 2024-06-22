from discord.ext import commands
import discord
from utils.mongo import Document


class Settings(Document):
    async def get(self, guild_id: int) -> dict:
        """
        Get the settings for a guild.
        :param guild_id (str): The ID of the guild.
        :return (dict): The settings.
        """
        return await self.find_by_id(guild_id)