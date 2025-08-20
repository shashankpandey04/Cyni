import discord
from discord.ext import commands

from datetime import  timedelta
import datetime
import re
import uuid
from utils.constants import BLANK_COLOR
import requests

from Database.Mongo import mongo_db

async def get_prefix(bot, message):
    """
    Get the prefix for the bot.
    :param bot (Bot): The bot.
    :param message (discord.Message): The message.
    :return (str): The prefix.
    """
    settings = await bot.settings.find_by_id(message.guild.id)
    
    if settings is None:
        return commands.when_mentioned_or("?")(bot,message)
    try:
        prefix = None
        customization = settings.get("customization")
        if customization is None:
            return commands.when_mentioned_or("?")(bot,message)
        if bot.is_premium:
            if customization.get("premium_prefix"):
                prefix = customization.get("premium_prefix")
        else:
            prefix = customization.get("prefix")
            if prefix is None:
                return commands.when_mentioned_or("?")(bot,message)
        return prefix
    except KeyError:
        return commands.when_mentioned_or("?")(bot,message)

def gen_error_uid():
    """
    Generate a unique error ID.
    :return (str): The unique error ID.
    """
    return str(uuid.uuid4().hex[:6])

def discord_time(dt):
    """
    Convert a datetime object to a Discord timestamp.
    :param dt (datetime): The datetime object.
    :return (str): The Discord timestamp.
    """
    unix_timestamp = int(dt.timestamp())
    return f"<t:{unix_timestamp}:R>"

def parse_duration(duration):
    """
    Parse a duration string and return the total duration in seconds.
    Supports days (d), weeks (w), hours (h), minutes (m), and seconds (s).
    """
    regex = r"(?:(\d+)\s*d(?:ays?)?)?\s*(?:(\d+)\s*w(?:eeks?)?)?\s*(?:(\d+)\s*h(?:ours?)?)?\s*(?:(\d+)\s*m(?:inutes?)?)?\s*(?:(\d+)\s*s(?:econds?)?)?"
    matches = re.match(regex, duration)
    if not matches:
        return None

    days = int(matches.group(1)) if matches.group(1) else 0
    weeks = int(matches.group(2)) if matches.group(2) else 0
    hours = int(matches.group(3)) if matches.group(3) else 0
    minutes = int(matches.group(4)) if matches.group(4) else 0
    seconds = int(matches.group(5)) if matches.group(5) else 0

    total_seconds = timedelta(days=days, weeks=weeks, hours=hours, minutes=minutes, seconds=seconds).total_seconds()
    return int(total_seconds)

async def log_command_usage(bot, guild, member, command_name):
    try:
        settings = await bot.settings.find_by_id(guild.id)
        if not settings:
            return
        if not settings.get('server_management', {}).get('cyni_log_channel'):
            return
        try:
            log_channel_id = settings.get('server_management', {}).get('cyni_log_channel')
        except (ValueError, TypeError):
            return
        log_channel = guild.get_channel(log_channel_id)
        if log_channel is None:
            return
        if not log_channel.permissions_for(guild.me).send_messages:
            return
        embed = discord.Embed(
            title="Cyni Command Log",
            description=f"Command `{command_name}` used by {member.mention}",
            color=BLANK_COLOR
        )
        embed.set_footer(text=f"User ID: {member.id}")
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await log_channel.send(embed=embed)
    except Exception as e:
        print(e)

async def config_change_log(bot,guild,member,data):
    setting = await bot.settings.find_by_id(guild.id)
    if not setting:
        return
    if not setting.get('server_management', {}).get('cyni_log_channel'):
        return
    try:
        log_channel_id = setting.get('server_management', {}).get('cyni_log_channel')
    except (ValueError,TypeError) as e:
        return
    log_channel = guild.get_channel(log_channel_id)
    if log_channel is None:
        return
    if not log_channel.permissions_for(guild.me).send_messages:
        return
    embed = discord.Embed(
        title="Cyni Config Change Log",
        description=f"Configuration change made by {member.mention}",
        color=BLANK_COLOR
    ).add_field(name="Configuration Change",value=data)
    embed.set_footer(text=f"User ID: {member.id}")
    embed.set_author(name=member.name, icon_url=member.display_avatar.url)
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    await log_channel.send(embed=embed)

async def create_full_backup(guild, bot):
    """
    Create a comprehensive backup of the guild, including roles, channels, categories,
    permissions, settings, and other relevant data for template restoration.
    
    Args:
        guild (discord.Guild): The guild to back up.
        bot (commands.Bot): The bot instance.
    
    Returns:
        dict: Backup data including backup ID and mappings.
    """
    backup_data = {
        "_id": guild.id,
        "guild_name": guild.name,
        "guild_owner_id": guild.owner_id,
        "icon_url": guild.icon.url if guild.icon else None,
        "roles": [],
        "categories": [],
        "channels": [],
        "emojis": [],
        "features": list(guild.features),
        "afk_channel_id": guild.afk_channel.id if guild.afk_channel else None,
        "afk_timeout": guild.afk_timeout,
        "system_channel_id": guild.system_channel.id if guild.system_channel else None,
        "verification_level": guild.verification_level.value,
        "explicit_content_filter": guild.explicit_content_filter.value,
        "default_notifications": guild.default_notifications.value,
        "banner_url": guild.banner.url if guild.banner else None,
        "splash_url": guild.splash.url if guild.splash else None,
        "created_at": guild.created_at.isoformat(),
    }

    for role in guild.roles:
        role_data = {
            "id": role.id,
            "name": role.name,
            "permissions": role.permissions.value,
            "color": role.color.value,
            "hoist": role.hoist,
            "position": role.position,
            "mentionable": role.mentionable,
            "managed": role.managed
        }
        backup_data["roles"].append(role_data)

    for category in guild.categories:
        category_data = {
            "id": category.id,
            "name": category.name,
            "position": category.position,
            "permissions": [
                {
                    "target_id": ow.target.id,
                    "target_type": type(ow.target).__name__,
                    "allow": ow.allow.value,
                    "deny": ow.deny.value
                }
                for ow in category.overwrites.values()
            ]
        }
        backup_data["categories"].append(category_data)

        for channel in category.channels:
            channel_data = {
                "id": channel.id,
                "type": channel.type.name,
                "name": channel.name,
                "position": channel.position,
                "nsfw": getattr(channel, "nsfw", False),
                "slowmode_delay": getattr(channel, "slowmode_delay", 0),
                "topic": getattr(channel, "topic", None),
                "category_id": category.id,
                "permissions": [
                    {
                        "target_id": ow.target.id,
                        "target_type": type(ow.target).__name__,
                        "allow": ow.allow.value,
                        "deny": ow.deny.value
                    }
                    for ow in channel.overwrites.values()
                ]
            }
            backup_data["channels"].append(channel_data)

    for channel in guild.channels:
        if channel.category is None:
            channel_data = {
                "id": channel.id,
                "type": channel.type.name,
                "name": channel.name,
                "position": channel.position,
                "nsfw": getattr(channel, "nsfw", False),
                "slowmode_delay": getattr(channel, "slowmode_delay", 0),
                "topic": getattr(channel, "topic", None),
                "category_id": None,
                "permissions": [
                    {
                        "target_id": ow.target.id,
                        "target_type": type(ow.target).__name__,
                        "allow": ow.allow.value,
                        "deny": ow.deny.value
                    }
                    for ow in channel.overwrites.values()
                ]
            }
            backup_data["channels"].append(channel_data)

    for emoji in guild.emojis:
        backup_data["emojis"].append({
            "id": emoji.id,
            "name": emoji.name,
            "animated": emoji.animated,
            "url": str(emoji.url)
        })

    await bot.backup.update_by_id(backup_data)

    return {
        "_id": guild.id,
        "guild_owner_id": guild.owner_id,
        "guild_name": guild.name
    }

def compare_overwrites(before_overwrites, after_overwrites):
    """
    Compare two sets of permission overwrites and return the differences.
    
    Parameters:
    -----------
    before_overwrites : dict
        The previous permission overwrites
    after_overwrites : dict
        The new permission overwrites
        
    Returns:
    --------
    list
        A list of tuples containing (target, perm_type, permission_name, old_value, new_value)
    """
    changes = []
    
    # Find all targets (roles/members) that exist in either overwrite set
    all_targets = set(before_overwrites.keys()) | set(after_overwrites.keys())
    
    for target in all_targets:
        # Get the overwrite objects (or None if they don't exist)
        before_overwrite = before_overwrites.get(target, None)
        after_overwrite = after_overwrites.get(target, None)
        
        # If target was added or removed entirely
        if before_overwrite is None:
            # Target was added
            for perm_name, value in after_overwrite:
                if value is not None:  # Only include non-default permissions
                    changes.append((target, "added", perm_name, None, value))
        elif after_overwrite is None:
            # Target was removed
            for perm_name, value in before_overwrite:
                if value is not None:  # Only include non-default permissions
                    changes.append((target, "removed", perm_name, value, None))
        else:
            # Target exists in both, compare permissions
            before_perms = dict(before_overwrite)
            after_perms = dict(after_overwrite)
            
            # Find all permission names
            all_perm_names = set(before_perms.keys()) | set(after_perms.keys())
            
            for perm_name in all_perm_names:
                before_value = before_perms.get(perm_name, None)
                after_value = after_perms.get(perm_name, None)
                
                if before_value != after_value:
                    changes.append((target, "changed", perm_name, before_value, after_value))
    
    return changes

async def get_discord_by_roblox(bot,username):
    api_url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": True}
    response = requests.post(api_url, json=payload)
    if response.status_code == 200:
        data = response.json()["data"][0]
        id = data["id"]
        linked_account = await bot.oauth2_users.db.find_one({"roblox_id": id})
        if linked_account:
            return linked_account["discord_id"]
        else:
            return None
        
def parse_duration(duration):
    """
    Parse a duration string and return the total duration in seconds.
    Supports days (d), weeks (w), hours (h), minutes (m), and seconds (s).
    """
    regex = r"(?:(\d+)\s*d(?:ays?)?)?\s*(?:(\d+)\s*w(?:eeks?)?)?\s*(?:(\d+)\s*h(?:ours?)?)?\s*(?:(\d+)\s*m(?:inutes?)?)?\s*(?:(\d+)\s*s(?:econds?)?)?"
    matches = re.match(regex, duration)
    if not matches:
        return None

    days = int(matches.group(1)) if matches.group(1) else 0
    weeks = int(matches.group(2)) if matches.group(2) else 0
    hours = int(matches.group(3)) if matches.group(3) else 0
    minutes = int(matches.group(4)) if matches.group(4) else 0
    seconds = int(matches.group(5)) if matches.group(5) else 0

    total_seconds = timedelta(days=days, weeks=weeks, hours=hours, minutes=minutes, seconds=seconds).total_seconds()
    return int(total_seconds)

def time_converter(parameter: str) -> int:
    conversions = {
        ("s", "seconds", " seconds"): 1,
        ("m", "minute", "minutes", " minutes"): 60,
        ("h", "hour", "hours", " hours"): 60 * 60,
        ("d", "day", "days", " days"): 24 * 60 * 60,
        ("w", "week", " weeks"): 7 * 24 * 60 * 60
    }

    for aliases, multiplier in conversions.items():
        parameter = parameter.strip()
        for alias in aliases:
            if parameter[(len(parameter) - len(alias)):].lower() == alias.lower():
                alias_found = parameter[(len(parameter) - len(alias)):]
                number = parameter.split(alias_found)[0]
                number = number.replace("-", "")
                if not number.strip()[-1].isdigit():
                    continue
                return int(number.strip()) * multiplier

    raise ValueError("Invalid time format")

def parse_color(hex_or_int) -> discord.Color:
    if isinstance(hex_or_int, int):
        return discord.Color(hex_or_int)
    if isinstance(hex_or_int, str) and hex_or_int.startswith("#"):
        return discord.Color(int(hex_or_int.strip("#"), 16))
    return discord.Color.default()

def generate_embed(
    guild: discord.Guild,
    title: str,
    category: str = "general",
    description: str = None,
    fields: list = None,
    footer: str = None,
    timestamp: bool = False,
    premium: bool = False,
    custom_colors: dict = None
) -> discord.Embed:
    category_colors = {
        "logging": discord.Color.yellow(),
        "moderation": discord.Color.red(),
        "info": discord.Color.blurple(),
        "success": discord.Color.green(),
        "error": discord.Color.dark_red(),
        "general": discord.Color.dark_gray(),
        "automod": discord.Color.teal(),
        "customization": discord.Color.purple(),
    }

    if premium and custom_colors:
        custom_hex = custom_colors.get(category.lower())
        if custom_hex:
            color = parse_color(custom_hex)
        else:
            color = category_colors.get(category.lower(), discord.Color.dark_gray())
    else:
        color = category_colors.get(category.lower(), discord.Color.dark_gray())

    embed = discord.Embed(title=title, description=description or "", color=color)

    if fields:
        for field in fields:
            embed.add_field(
                name=field.get("name", "—"),
                value=field.get("value", "—"),
                inline=field.get("inline", False)
            )

    if premium:
        embed.set_footer(text=f"{footer if footer else ''}", icon_url=guild.icon.url if guild.icon else None)
    else:
        embed.set_footer(text=f"{footer if footer else ''} | By Cyni", icon_url=guild.icon.url if guild.icon else None)

    if timestamp:
        embed.timestamp = datetime.utcnow()

    return embed
