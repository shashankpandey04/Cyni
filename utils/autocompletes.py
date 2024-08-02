import discord
from discord import app_commands
from discord.ext import commands
import typing

from discord.ext.commands import Context

async def infraction_autocomplete(
        interaction: discord.Interaction,_:str
) -> typing.List[app_commands.Choice[str]]:
    bot = interaction.client

    data = await bot.infraction_types.find_by_id(interaction.guild.id)
    if data is None:
         return [
            app_commands.Choice(
                name="Promotion",
                value="promotion"
            ),
            app_commands.Choice(
                name="Demotion",
                value="demotion"
            ),
            app_commands.Choice(
                name="Warning",
                value="warning"
            ),
        ]
    
    infraction_types = data["infraction_types"]
    types = infraction_types.get('type', [])

    if types is not None and len(types or []) != 0:
        return [
            app_commands.Choice(
                name=infract_type,
                value=infract_type
            )
            for infract_type in types
        ]
    else:
        return [
            app_commands.Choice(
                name="Promotion",
                value="promotion"
            ),
            app_commands.Choice(
                name="Demotion",
                value="demotion"
            ),
            app_commands.Choice(
                name="Warning",
                value="warning"
            ),
        ]
    
async def application_autocomplete(
        interaction: discord.Interaction,_:str
) -> typing.List[app_commands.Choice[str]]:
    return [
        app_commands.Choice(
            name="Accepted",
            value="accepted"
        ),
        app_commands.Choice(
            name="Declined",
            value="declined"
        )
    ]