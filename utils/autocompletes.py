import discord
from discord import app_commands
import asyncio
import aiohttp
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

async def dm_autocomplete(
        interaction: discord.Interaction,_:str
) -> typing.List[app_commands.Choice[str]]:
    return [
        app_commands.Choice(
            name="Yes",
            value="true"
        ),
        app_commands.Choice(
            name="No",
            value="false"
        )
    ]

async def application_type_autocomplete(
        interaction: discord.Interaction,_:str
) -> typing.List[app_commands.Choice[str]]:
    bot = interaction.client

    data = await bot.applications.find_by_id(interaction.guild.id)
    if data is None:
         return [
            app_commands.Choice(
                name="None",
                value="None"
            )
        ]
    
    applications_types = data["applications"]
    types = applications_types.get('name', [])

    if types is not None and len(types or []) != 0:
        return [
            app_commands.Choice(
                name=application_type,
                value=application_type
            )
            for application_type in types
        ]
    else:
        return [
            app_commands.Choice(
                name="None",
                value="None"
            )
        ]
    
async def shift_type_autocomplete(
        interaction: discord.Interaction,_:str
) -> typing.List[app_commands.Choice[str]]:
    bot = interaction.client

    data = await bot.shift_types.find_by_id(interaction.guild.id)
    if data is None:
        return [
            app_commands.Choice(
                name="Default",
                value="default"
            ),
        ]

    shift_types = list(data.keys()) if isinstance(data, dict) else []

    if shift_types and len(shift_types) != 0:
        return [
            app_commands.Choice(
                name=shift_type,
                value=shift_type
            )
            for shift_type in shift_types
        ]
    else:
        return [
            app_commands.Choice(
                name="Default",
                value="default"
            ),
        ]

async def punishment_autocomplete(
    interaction: discord.Interaction, current: str
) -> typing.List[app_commands.Choice[str]]:
    bot = interaction.client
    Data = await bot.punishment_types.find_by_id(interaction.guild.id)
    default_punishments = ["Warning", "Kick", "Ban", "Bolo"]
    enabled_punishments = None
    if Data is None:
        return [
            app_commands.Choice(name=item, value=item)
            for item in default_punishments
        ]
        enabled_punishments = Data.get("default_punishments", [])
    else:
        ndt = []
        for item in Data["types"]:
            if item not in default_punishments:
                ndt.append(item)
        enabled_defaults = {
            p["name"].lower()
            for p in enabled_punishments
            if p.get("enabled", False)
        }
        filtered_punishments = [
            name.capitalize() for name in ["warning", "kick", "ban", "bolo"] if name in enabled_defaults
        ]
        return [
            app_commands.Choice(
                name=(
                    item_identifier := item if isinstance(item, str) else item["name"]
                ),
                value=item_identifier,
            )
            for item in ndt + filtered_punishments
        ]



last_request_time = {}

async def fetch_roblox_users(query: str):
    url = f"https://apis.roblox.com/search-api/omni-search?verticalType=user&searchQuery={query}&pageToken=&globalSessionId=547118cc-0912-4080-ad3d-df835d0f9f5a&sessionId=547118cc-0912-4080-ad3d-df835d0f9f5a"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            try:
                return data["searchResults"][0]["contents"]
            except (KeyError, IndexError):
                return []


username_cache = {}

async def username_autocomplete(
    interaction: discord.Interaction, current: str
) -> typing.List[app_commands.Choice[str]]:
    guild_id = interaction.guild.id
    if guild_id not in username_cache:
        username_cache[guild_id] = []

    if not current:
        # Return cached usernames if no input is provided
        return [
            app_commands.Choice(
                name=f"{user['display_name']} (@{user['username']})",
                value=user['username']
            )
            for user in username_cache[guild_id]
        ]

    if len(current) < 4:
        return [app_commands.Choice(name="Type at least 4 characters", value="")]

    user_id = interaction.user.id
    now = asyncio.get_event_loop().time()
    if user_id in last_request_time and now - last_request_time[user_id] < 1.0:
        return []
    last_request_time[user_id] = now

    results = await fetch_roblox_users(current)
    choices = []
    for user in results[:10]:
        username = user.get("username")
        display_name = user.get("displayName", username)
        if username:
            choices.append(
                app_commands.Choice(
                    name=f"{display_name} (@{username})",
                    value=username
                )
            )
            # Add to cache
            if len(username_cache[guild_id]) >= 25:
                username_cache[guild_id].pop(0)
            username_cache[guild_id].append({
                "username": username,
                "display_name": display_name
            })

    return choices
