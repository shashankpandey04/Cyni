import discord
from discord.ext import commands

from datetime import  timedelta
import datetime
import re
import pytz
import uuid
from utils.constants import BLANK_COLOR

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
    # Convert datetime to a Unix timestamp
    unix_timestamp = int(dt.timestamp())
    # Return the Discord formatted timestamp
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
    Create a full backup of the guild's settings, roles, channels, categories, and permissions,
    including additional data from various collections.
    
    Args:
    guild (discord.Guild): The guild to back up.
    bot (commands.Bot): The bot instance.
    
    Returns:
    dict: Backup data including backup ID and ID mappings.
    """
    backup_data = {
        "_id": guild.id,
        "guild_name": guild.name,
        "guild_owner_id": guild.owner_id,
        "roles": [],
        "categories": [],
        "channels": [],
        "permissions": [],
        "settings": {},
        "staff_activity": [],
        "infraction_logs": [],
        "warnings": []
    }

    for role in guild.roles:
        role_data = {
            "name": role.name,
            "permissions": list(role.permissions),
            "color": role.color.value,
            "hoist": role.hoist,
            "position": role.position
        }
        backup_data["roles"].append(role_data)

    for category in guild.categories:
        category_data = {
            "id": category.id,
            "name": category.name,
            "position": category.position
        }
        backup_data["categories"].append(category_data)
        
        for channel in category.channels:
            channel_data = {
                "id": channel.id,
                "type": channel.type.name,
                "name": channel.name,
                "position": channel.position,
                "nsfw": channel.nsfw,
                "slowmode_delay": channel.slowmode_delay,
                "category_id": category.id
            }
            backup_data["channels"].append(channel_data)

    settings = await bot.settings.find_one({"_id": guild.id})
    if settings:
        backup_data["settings"] = settings

    staff_activity = await bot.staff_activity.find_one({"_id": guild.id})
    if staff_activity:
        backup_data["staff_activity"] = staff_activity.get("staff", [])

    infraction_logs = await bot.infraction_log.find({"_id": guild.id})
    for log in infraction_logs:
        backup_data["infraction_logs"].extend(log.get("staff", []))

    warnings_cursor = await bot.warnings.find({"_id": {"$regex": f"^{guild.id}-"}})
    for warning in warnings_cursor:
        backup_data["warnings"].append(warning)

    await bot.backup.update_by_id(backup_data)

    return {
        "_id": guild.id,
        "guild_owner_id": guild.owner_id
    }

def compare_overwrites(before_overwrites, after_overwrites):
    changes = []
    all_targets = set(before_overwrites.keys()).union(set(after_overwrites.keys()))
    for target in all_targets:
        before_perms = before_overwrites.get(target, discord.PermissionOverwrite())
        after_perms = after_overwrites.get(target, discord.PermissionOverwrite())
        perm_changes = []
        for perm in discord.Permissions.VALID_FLAGS:
            before_value = getattr(before_perms, perm, None)
            after_value = getattr(after_perms, perm, None)
            if before_value != after_value:
                status_before = "Allowed" if before_value is True else "Denied" if before_value is False else "Neutral"
                status_after = "Allowed" if after_value is True else "Denied" if after_value is False else "Neutral"
                perm_changes.append(f"{perm}: {status_before} -> {status_after}")
        if perm_changes:
            changes.append(f"{target.name}:\n" + "\n".join(perm_changes))

    return changes