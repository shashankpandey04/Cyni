import discord
from discord.ext import commands
import datetime
import json
import os
#import keep_alive
import requests
import sys
import traceback
import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!",intents=intents)

dev_username = ['itsme.tony']
staff_username = ['tearispro']
SUPPORT_SERVER_CHANNEL_ID = 1164559668610355281

try:
    with open('warnings.json', 'r') as warnings_file:
        warnings = json.load(warnings_file)
except FileNotFoundError:
    warnings = {}

def save_data():
    with open('warnings.json', 'w') as warnings_file:
        json.dump(warnings, warnings_file, indent=4)

CONFIG_FILE = "server_config.json"

def load_config():
    """Load server configuration from server_config.json file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}

def save_config(config):
    """Save server configuration to server_config.json file."""
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

def get_server_config(guild_id):
    """Get server configuration for a specific guild."""
    config = load_config()
    return config.get(str(guild_id), {})

def update_server_config(guild_id, data):
    """Update server configuration for a specific guild."""
    config = load_config()
    config[str(guild_id)] = data
    save_config(config)

def create_or_get_server_config(guild_id):
    """Create or get server configuration for a specific guild."""
    config = get_server_config(guild_id)
    if not config:
        config = {
            "staff_roles": [],
            "management_role": []
        }
        update_server_config(guild_id, config)
    return config

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    await bot.tree.sync()
    save_data()
    for guild in bot.guilds:
        create_or_get_server_config(guild.id)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/help"))
    await send_restart_message()

@bot.event
async def on_command_error(ctx, error):
    error_uid = "ERR" + str(hash(ctx.message.created_at))
    error_message = f"An error occurred (UID: {error_uid})! Please contact support."
    sentry=discord.Embed(title="Error",description=f"Error UID: {error_uid}\nThis can be solved by joining our support server at \n [Join Support Server](https://discord.gg/2D29TSfNW6)",color=0xFF0000)
    await ctx.send(embed = sentry)
    error_data = {
        "error_uid": error_uid,
        "command": ctx.message.content,
        "error": str(error),
        "traceback": ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    }
    with open('error.json', 'a') as json_file:
        json.dump(error_data, json_file)
        json_file.write('\n')

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    error_uid = "ERR" + str(hash(exc_value))
    logger.error(f"Error UID: {error_uid}\n{''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}")
    support_channel = bot.get_channel(SUPPORT_SERVER_CHANNEL_ID)
    if support_channel:
        error_message = f"Error UID: {error_uid}\n{''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}"
        support_channel.send(error_message)

sys.excepthook = handle_exception

async def send_restart_message():
  support_server = bot.get_guild(1152949579407442050)
  if not support_server:
      print('Support server not found.')
      return
  
  support_channel = support_server.get_channel(1164559668610355281)
  if not support_channel:
      print('Support channel not found.')
      return
  
  await support_channel.send('Bot has been restarted!')

@bot.tree.command()
async def changestatus(interaction: discord.Interaction, activity_type: str, *, status: str):
    '''Change  Status of Bot [Dev Access]'''
    if interaction.user.name in dev_username:
        if activity_type.lower() == "watching":
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status))
            await interaction.response.send_message("Status Changed!",ephemeral=True)
        elif activity_type.lower() == "playing":
            await bot.change_presence(activity=discord.Game(name=status))
            await interaction.response.send_message("Status Changed!",ephemeral=True)
        elif activity_type.lower() == "listening":
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status))
            await interaction.response.send_message("Status Changed!",ephemeral=True)
        else:
            await interaction.response.send_message("Invalid activity type. Available types: watching, playing, listening, streaming")
    else:
        await interaction.response.send_message("You do not have permission to change the bot's status.")

def get_staff_roles(guild_id):
    """Get staff roles for a specific guild."""
    config = load_config()
    return config.get(str(guild_id), {}).get("staff_roles", [])

def get_management_roles(guild_id):
    """Get management roles for a specific guild."""
    config = load_config()
    return config.get(str(guild_id), {}).get("management_role", [])

@bot.event
async def on_guild_join(guild):
    create_or_get_server_config()

@bot.tree.command()
async def help(interaction: discord.Interaction):
    '''Link to Support Server'''
    embed = discord.Embed(title="Need Assistance?",description=f"Join our Support Discord Server and our support team will help you with your problem. [Click Here](https://discord.gg/2D29TSfNW6) ",color=60407)
    await interaction.response.send_message(embed=embed)

@bot.tree.command()
async def cyniofficial(interaction: discord.Interaction):
    '''Get Cyni Official Role'''
    
    if interaction.guild.id == 1152949579407442050:
      await interaction.response.send_message("You cannot use this command in the support server.")
  
    elif (interaction.user.name in staff_username) or (interaction.user.name in dev_username):
        guild = interaction.guild
        role_name = "CYNI Official"

        user_roles = interaction.user.roles
        highest_role = max(user_roles, key=lambda role: role.position)

        role = discord.utils.get(guild.roles, name=role_name)
        
        if role is None:
            role = await guild.create_role(name=role_name, color=discord.Color.from_rgb(0, 255, 255))
        await role.edit(position=highest_role.position)
        await role.edit(position=highest_role.position, hoist=True)

        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"{interaction.user.name} is Official Staff of Cyni.")
        invite = await interaction.channel.create_invite()
        print(f"{interaction.user.name} got rolled in {interaction.guild.name}. Link to server: {invite}")
    else:
        await interaction.response.send_message("You are not authorized to use this command.")


@bot.tree.command()
async def staffroleadd(interaction: discord.Interaction, role: discord.Role):
    management_roles = get_management_roles(interaction.guild.id)
    if any(role.id in management_roles for role in interaction.user.roles) or (interaction.user.guild_permissions.administrator == True):
        '''Add a staff role to the server configuration'''
        try:
            with open("server_config.json", "r") as file:
                server_config = json.load(file)

            guild_id = str(interaction.guild.id)
            if "staff_roles" not in server_config[guild_id]:
                server_config[guild_id]["staff_roles"] = []

            server_config[guild_id]["staff_roles"].append(role.id)

            with open("server_config.json", "w") as file:
                json.dump(server_config, file, indent=4)
            embed = discord.Embed(title="Server Config Changed", description=f"Added {role.mention} as a staff role.",color=0x0000FF)
            await interaction.response.send_message(embed=embed)
        except:
            await interaction.response.send_message("Some Internal Error occured.")
    else:
        await interaction.response.send_message("You don't have permission to use this command.")

@bot.tree.command()
@commands.has_permissions(administrator=True)
async def managementadd(interaction: discord.Interaction, role: discord.Role):
    '''Add a staff role to the server configuration'''
    if interaction.user.guild_permissions.administrator == True:
        try:
            with open("server_config.json", "r") as file:
                server_config = json.load(file)

            guild_id = str(interaction.guild.id)
            if "management_role" not in server_config[guild_id]:
                server_config[guild_id]["management_role"] = []

            if role.id not in server_config[guild_id]["management_role"]:
                server_config[guild_id]["management_role"].append(role.id)

                with open("server_config.json", "w") as file:
                    json.dump(server_config, file, indent=4)
                embed = discord.Embed(title="Server Config Changed", description=f"Added {role.mention} as a Management role.",color=0x0000FF)
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title="Server Config Unchanged", description=f"{role.mention} is already a Management role.",color=0xFF0000)
                await interaction.response.send_message(embed=embed)
        except:
            await interaction.response.send_message("Some Internal Error occured.")
    else:
        await interaction.response.send_message("You don't have permission to use this command.")

@bot.tree.command()
@commands.has_permissions(administrator=True)
async def staffroleremove(interaction: discord.Interaction, role: discord.Role):
    '''Remove Staff Role from server.'''
    manegement_roles = get_management_roles(interaction.guild.id)
    if any(role.id in manegement_roles for role in interaction.user.roles) or (interaction.user.guild_permissions.administrator == True):
        try:
            guild_id = str(interaction.guild.id)
            with open("server_config.json", "r") as file:
                server_config = json.load(file)

            if "staff_roles" not in server_config[guild_id]:
                server_config[guild_id]["staff_roles"] = []

            if role.id in server_config[guild_id]["staff_roles"]:
                server_config[guild_id]["staff_roles"].remove(role.id)

                with open("server_config.json", "w") as file:
                    json.dump(server_config, file, indent=4)

                await interaction.response.send_message(f"Removed {role.mention} from staff roles.")
            else:
                await interaction.response.send_message(f"{role.mention} is not in the staff roles list.")
        except Exception as e:
            print(e)
            await interaction.response.send_message(f"Failed to remove {role.mention} from staff roles.")
    else:
        await interaction.response.send_message("You don't have permission to use this command.")

@bot.tree.command()
@commands.has_permissions(administrator=True)
async def managementremove(interaction: discord.Interaction, role: discord.Role):
    '''Remove Management Role from server.'''
    if interaction.user.guild_permissions.administrator == True:
        try:
            guild_id = str(interaction.guild.id)
            with open("server_config.json", "r") as file:
                server_config = json.load(file)

            if "management_role" not in server_config[guild_id]:
                server_config[guild_id]["management_roles"] = []

            if role.id in server_config[guild_id]["management_role"]:
                server_config[guild_id]["management_role"].remove(role.id)

                with open("server_config.json", "w") as file:
                    json.dump(server_config, file, indent=4)
                embed = discord.Embed(title="Server Config Changed",description=f"Removed {role.mention} from staff roles.")
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title="Server Config Error",description=f"{role.mention} is not in the staff roles list.")
                await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(e)
            await interaction.response.send_message("Some Internal Error occured.")
    else:
        await interaction.response.send_message("You don't have permission to use this command.")

@bot.tree.command()
async def get_error(interaction: discord.Interaction, error_uid: str):
    '''Error Log directory'''
    if interaction.user.name not in dev_username:
        await interaction.response.send_message("You don't have permission to access error logs.")
        return
    error_data = []
    with open('error.json', 'r') as json_file:
        for line in json_file:
            error_data.append(json.loads(line))
    found_error = None
    for error_entry in error_data:
        if error_entry["error_uid"] == error_uid:
            found_error = error_entry
            break
    if found_error:
        traceback_value = found_error['traceback'][:1000]
        error_embed = discord.Embed(
            title=f"Error UID: {found_error['error_uid']}",
            description="Error details:",
            color=discord.Color.red())
        error_embed.add_field(name="Command", value=found_error["command"], inline=False)
        error_embed.add_field(name="Error", value=found_error["error"], inline=False)
        error_embed.add_field(name="Traceback", value=f"```{traceback_value}```", inline=False)
        await interaction.response.send_message(embed=error_embed)
    else:
        await interaction.response.send_message(f"Error UID '{error_uid}' not found in error logs.")

@bot.tree.command()
async def say(interaction: discord.Interaction, message: str):
    '''Broadcasts a message in the channel'''
    channel = interaction.channel
    try:
        await interaction.response.send_message("Message sent.",ephemeral=True)
        await channel.send(message)
    except:
        await channel.send('Failed to process command.')

@bot.tree.command()
async def slowmode(interaction: discord.Interaction, duration: str):
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600
    }
    guild_id = interaction.guild.id
    management_role = get_management_roles(guild_id)
    staff_roles = get_staff_roles(guild_id)
    if not any(role.id in management_role for role in interaction.user.roles) or any(role.id in staff_roles for role in interaction.user.roles):
            await interaction.response.send_message("❌ Missing permissions to use the command.")
    else:
        try:
            amount = int(duration[:-1])
            unit = duration[-1]
            if unit not in time_units:
                raise ValueError
        except (ValueError, IndexError):
            await interaction.response.send_message('Invalid duration format. Please use a number followed by "s" for seconds, "m" for minutes, or "h" for hours.')
            return
        total_seconds = amount * time_units[unit]
        if total_seconds == 0:
            await interaction.response.send_message("Slow mode disabled from the channel.")
        elif total_seconds > 21600:
            await interaction.response.send_message('Slow mode duration cannot exceed 6 hours (21600 seconds).')
            return
        else:
            await interaction.channel.edit(slowmode_delay=total_seconds)
            await interaction.response.send_message(f'Slow mode set to {amount} {unit} in this channel.')

@bot.tree.command()
async def ping(interaction: discord.Interaction):
    '''Check the bot's ping.'''
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'Pong! Latency: {latency}ms')

@bot.tree.command()
async def roleadd(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    '''Add a role to member'''
    guild_id = interaction.guild.id
    staff_roles = get_staff_roles(guild_id)
    managment_role = get_management_roles(guild_id)
    if not any(role.id in staff_roles for role in interaction.user.roles) or any(role.id in managment_role for role in interaction.user.roles):
        if interaction.guild.me.top_role <= role:
            await interaction.response.send_message("Sorry, I don't have permission to add this role.")
        elif interaction.user.top_role <= role:
            await interaction.response.send_message("You can't add a role higher than you.")
        else:
            await member.add_roles(role)
            embed = discord.Embed(title='Role added.',description=f"Role {role.mention} add to {member.mention}",color=0x00FF00)
            await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("You don't have permission to use this command.")

@bot.tree.command()
async def roleremove(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    '''Removes a role from member'''
    guild_id = interaction.guild.id
    staff_roles = get_staff_roles(guild_id)
    manaement_roles = get_management_roles(guild_id)
    if not any(role.id in staff_roles for role in interaction.user.roles) or any(role.id in manaement_roles for role in interaction.user.roles):
        if interaction.guild.me.top_role <= role:
            await interaction.response.send_message("Sorry, I don't have permission to remove this role.")
        elif interaction.user.top_role <= role:
            await interaction.response.send_message("You can't remove a role higher than you.")
        else:
            await member.remove_roles(role)
            embed = discord.Embed(title='Role Removed.',description=f"Role {role.mention} is now removed from {member.mention}",color=0xFF0000)
            await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("You don't have permission to use this command.")

@bot.tree.command()
async def kick(interaction: discord.Interaction, member: discord.Member, *, reason: str):
    '''Kicks user from server'''
    guild_id = interaction.guild.id
    staff_roles = get_staff_roles(guild_id)
    management_roles = get_management_roles(guild_id)
    if not any(role.id in staff_roles for role in interaction.user.roles) or not any(role.id in management_roles for role in interaction.user.roles):
        embed = discord.Embed(title="Kick Denied", description="You don't have permission to use this command.", color=0xFF0000)
        await interaction.response.send_message(embed=embed)
        return
    elif interaction.guild.me.top_role <= member.top_role:
        embed = discord.Embed(title='Kick Failed', description="Sorry, I don't have permission to kick users higher than me.", color=0XFF0000)
        await interaction.response.send_message(embed=embed)
    elif interaction.user.top_role <= member.top_role:
        embed = discord.Embed(title="Kick Denied", description="You can't kick users with higher roles.", color=0xFF0000)
        await interaction.response.send_message(embed=embed)
    else:
        kick_embed = discord.Embed(
            title='User Kicked', description=f"User {member} got kicked for {reason}", color=0xFF0000,)
        kick_embed.set_footer(text=datetime.datetime.utcnow())
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(embed=kick_embed)
        except discord.Forbidden:
            fail_embed = discord.Embed(title="Kick Failed", description=f"You can't kick {member.mention}.")
            await interaction.response.send_message(embed=fail_embed)

@bot.tree.command()
async def ban(interaction: discord.Interaction, member: discord.Member, *, reason: str):
    '''Ban user from server'''
    guild_id = interaction.guild.id
    staff_roles = get_staff_roles(guild_id)
    management_roles = get_management_roles(guild_id)
    if not any(role.id in staff_roles for role in interaction.user.roles) or not any(role.id in management_roles for role in interaction.user.roles):
        embed = discord.Embed(title="Ban Denied", description="You don't have permission to use this command.", color=0xFF0000)
        await interaction.response.send_message(embed=embed)
        return
    elif interaction.guild.me.top_role <= member.top_role:
        embed = discord.Embed(title='Ban Failed', description="Sorry, I don't have permission to Ban users higher than me.", color=0XFF0000)
        await interaction.response.send_message(embed=embed)
    elif interaction.user.top_role <= member.top_role:
        embed = discord.Embed(title="Ban Denied", description="You can't Ban users with higher roles.", color=0xFF0000)
        await interaction.response.send_message(embed=embed)
    else:
        kick_embed = discord.Embed(
            title='User Banned', description=f"User {member} got banned for {reason}", color=0xFF0000,)
        kick_embed.set_footer(text=datetime.datetime.utcnow())
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(embed=kick_embed)
        except discord.Forbidden:
            fail_embed = discord.Embed(title="Ban Failed", description=f"You can't Ban {member.mention}.")
            await interaction.response.send_message(embed=fail_embed)

def get_next_case_number(guild_id, user_id):
    try:
        with open('warnings.json', 'r') as file:
            warnings = json.load(file)
            if guild_id in warnings and user_id in warnings[guild_id]:
                user_warnings = warnings[guild_id][user_id]
                # Find the highest existing case number for the user
                existing_case_numbers = [warning['case_number'] for warning in user_warnings]
                if existing_case_numbers:
                    next_case_number = max(existing_case_numbers) + 1
                else:
                    next_case_number = 1
                user_warnings.append({
                    "case_number": next_case_number,
                    "reason": "New case reason",
                    "date": "Current date and time"
                })
                with open('warnings.json', 'w') as json_file:
                    json.dump(warnings, json_file, indent=4)
                return next_case_number
            else:
                warnings.setdefault(guild_id, {}).setdefault(user_id, [])
                warnings[guild_id][user_id].append({
                    "case_number": 1,
                    "reason": "New case reason",
                    "date": "Current date and time"
                })
                with open('warnings.json', 'w') as json_file:
                    json.dump(warnings, json_file, indent=4)
                return 1
    except FileNotFoundError:
        print("Error: warnings.json file not found.")
        return 1
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in warnings.json.")
        return 1

@bot.tree.command()
async def warn(interaction: discord.Interaction, user: discord.User, *, reason: str):
    '''Log warning against user in server.'''
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    guild_id = str(interaction.guild.id)
    user_id = str(user.id)
    case_number = get_next_case_number(guild_id, user_id)
    staff_roles = get_staff_roles(guild_id)
    management_roles = get_management_roles(guild_id)
    if not any(role.id in staff_roles for role in interaction.user.roles) or not any(role.id in management_roles for role in interaction.user.roles):
        embed = discord.Embed(title="Warn Denied", description="You don't have permission to use this command.", color=0xFF0000)
        await interaction.response.send_message(embed=embed)
        return
    elif staff_roles or management_roles:
        user_roles = [role.id for role in user.roles]
        if any(role_id in user_roles for role_id in staff_roles):
            if guild_id not in warnings:
                warnings[guild_id] = {}
            if user_id not in warnings[guild_id]:
                warnings[guild_id][user_id] = []
            warnings[guild_id][user_id].append({
                'case_number': case_number,
                'reason': reason,
                'date': current_datetime
            })
            save_data()
            embed = discord.Embed(title="User Warned", description=f"{user.mention} got warned for {reason}. Case Number: {case_number}", color=0xFF0000)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message('❌ You do not have permission to use this command.')
    else:
        await interaction.response.send_message('❌ Staff roles are not defined in the server configuration.')

@bot.tree.command()
async def delwarn(interaction: discord.Interaction, user: discord.User, case_number: int):
    '''Delete a user warning.'''
    guild_id = interaction.guild.id
    staff_roles = get_staff_roles(guild_id)
    management_roles = get_management_roles(guild_id)
    if not any(role.id in staff_roles for role in interaction.user.roles) or not any (role.id in management_roles for role in interaction.user.roles):
        embed = discord.Embed(title="Kick Denied", description="You don't have permission to use this command.", color=0xFF0000)
        await interaction.response.send_message(embed=embed)
        return
    elif staff_roles or management_roles:
        user_roles = [role.id for role in interaction.user.roles]
        if any(role_id in user_roles for role_id in staff_roles):
            if str(interaction.guild.id) in warnings and str(user.id) in warnings[str(interaction.guild.id)]:
                user_warnings = warnings[str(interaction.guild.id)][str(user.id)]
                for warning in user_warnings:
                    if warning['case_number'] == case_number:
                        user_warnings.remove(warning)

                        # Reassign case numbers for remaining warnings
                        for i, warning in enumerate(user_warnings):
                            warning['case_number'] = i + 1

                        save_data()
                        embed = discord.Embed(title="User warning removed.", description=f"Warning number {case_number} removed from {user.mention}.", color=0x0000FF)
                        await interaction.response.send_message(embed=embed)
                        return
                embed = discord.Embed(title="Case not found.", description=f'Warning case #{case_number} not found for {user.mention}.', color=0xFF0000)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f'{user.mention} does not have any warnings.')

@bot.tree.command()
async def warnlog(interaction: discord.Interaction, user: discord.User):
    """View all warnings of a user in the guild."""
    guild_id = str(interaction.guild.id)
    user_id = str(user.id)
    if guild_id in warnings and user_id in warnings[guild_id]:
        user_warnings = warnings[guild_id][user_id]
        if user_warnings:
            embed = discord.Embed(title=f"Warnings for {user.name}#{user.discriminator}", color=discord.Color.red())
            for warning in user_warnings:
                embed.add_field(name=f"Case #{warning['case_number']}", value=f"**Reason:** {warning['reason']}\n**Date:** {warning['date']}", inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"{user.name}#{user.discriminator} has no warnings.")
    else:
        await interaction.response.send_message(f"No warnings found for {user.name}#{user.discriminator} in this guild.")

@bot.tree.command()
async def membercount(interaction: discord.Interaction):
    '''Gives the total number of members in server.'''
    embed = discord.Embed(description=f"{interaction.guild.member_count} members.",color=0x0F00FF)
    await interaction.response.send_message(embed=embed)

@bot.command()
async def membercount(interaction: discord.Interaction):
    '''Gives the total number of members in server.'''
    embed = discord.Embed(description=f"{interaction.guild.member_count} members.",color=0x00FF00)
    await interaction.channel.send(embed=embed)

@bot.tree.command()
async def promote(interaction: discord.Interaction, member: discord.Member, *,old_rank: discord.Role, next_rank: discord.Role, approved: discord.Role, reason: str):
    '''Promote Server Staff'''
    guild_id = interaction.guild.id
    managemet_role = get_management_roles(guild_id)
    if not any(role.id in managemet_role for role in interaction.user.roles):
      await interaction.response.send_message(
          "❌ You don't have permission to use this command.")
      return
    else:
      channel = interaction.channel
      embed = discord.Embed(title=f"{interaction.guild.name} Promotions.",
                            color=0x00FF00)
      embed.add_field(name="Staff Name", value=member.mention)
      embed.add_field(name="Old Rank", value=old_rank.mention)
      embed.add_field(name="New Rank", value=next_rank.mention)
      embed.add_field(name="Approved By", value=approved.mention)
      embed.add_field(name="Reason", value=reason)
      embed.add_field(name="Signed By", value=interaction.user.mention)
      await interaction.response.send_message("Promotion Sent", ephemeral=True)
      await channel.send(member.mention, embed=embed)

@bot.tree.command()
async def demote(interaction: discord.Interaction, member: discord.Member, *,old_rank: discord.Role, next_rank: discord.Role,approved: discord.Role, reason: str):
    '''Demote Server Staff'''
    guild_id = interaction.guild.id
    managemet_role = get_management_roles(guild_id)
    if not any(role.id in managemet_role for role in interaction.user.roles):
      await interaction.response.send_message(
          "❌ You don't have permission to use this command.")
      return
    else:
      channel = interaction.channel
      embed = discord.Embed(title=f"{interaction.guild.name} Demotions.",
                            color=0x00FF00)
      embed.add_field(name="Staff Name", value=member.mention)
      embed.add_field(name="Old Rank", value=old_rank.mention)
      embed.add_field(name="New Rank", value=next_rank.mention)
      embed.add_field(name="Approved By", value=approved.mention)
      embed.add_field(name="Reason", value=reason)
      embed.add_field(name="Signed By", value=interaction.user.mention)
      await interaction.response.send_message("Demotion Sent", ephemeral=True)
      await channel.send(member.mention, embed=embed)

@bot.command()
async def get_invite(ctx, guild_id: int):
    '''Get existing invite link for a specific guild'''
    guild = bot.get_guild(guild_id)
    if ctx.author.name in dev_username:
        if guild is not None:
            try:
                invites = await guild.invites()
                if invites:
                    invite = invites[0] 
                    await ctx.send(f"Existing invite link for {guild.name}: {invite.url}")
                else:
                    await ctx.send(f"No existing invite links found for {guild.name}.")
            except discord.errors.Forbidden:
                await ctx.send("Bot does not have permission to view invites in the specified guild.")
        else:
            await ctx.send("Bot is not a member of the specified guild.")
    else:
        await ctx.send("You do not have permission to use this command.")

@bot.command()
async def guildcount(ctx):
  if ctx.author.name in dev_username:
      '''Show the total number of guilds the bot is in'''
      guild_count = len(bot.guilds)
      await ctx.send(f"The bot is in {guild_count} guilds.")

api_url = "https://cyniai.quprsystems.repl.co/api"
CYNI_API_KEY = "12uyvehbwa gevg21iubhywihbehv21y9817f4ywub"
@bot.tree.command()
async def search(interaction: discord.Interaction, topic: str):
    '''Search on web using Cyni API'''
    params = {'topic': topic}
    headers = {'Authorization': f'Bearer {CYNI_API_KEY}'}

    try:
        response = requests.get(api_url, params=params, headers=headers)
        data = response.json()

        if response.status_code == 200:
            await interaction.response.send_message(f"**{data['topic']}**\n{data['result']}"+' | more on google.')
        else:
            await interaction.response.send_message(f"Error: {data['result']}")

    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}")

@bot.tree.command()
async def passapp(interaction: discord.Interaction, member: discord.Member, *,server_message: str,feedback: str):
    '''Post Passed Application Result'''
    guild_id = interaction.guild.id
    managemet_role = get_management_roles(guild_id)
    if not any(role.id in managemet_role for role in interaction.user.roles):
      await interaction.response.send_message(
          "❌ You don't have permission to use this command.")
      return
    else:
      channel = interaction.channel
      embed = discord.Embed(title=f"{interaction.guild.name} Application Passed.",color=0x00FF00)
      embed.add_field(name="Staff Name", value=member.mention)
      embed.add_field(name="Server Message", value=server_message)
      embed.add_field(name="Feedback", value=feedback)
      embed.add_field(name="Signed By", value=interaction.user.mention)
      await interaction.response.send_message("Result Sent", ephemeral=True)
      await channel.send(member.mention, embed=embed)

@bot.tree.command()
async def failapp(interaction: discord.Interaction, member: discord.Member, *,feedback: str):
    '''Post Failed Application Result'''
    guild_id = interaction.guild.id
    managemet_role = get_management_roles(guild_id)
    if not any(role.id in managemet_role for role in interaction.user.roles):
      await interaction.response.send_message(
          "❌ You don't have permission to use this command.")
      return
    else:
      channel = interaction.channel
      embed = discord.Embed(title=f"{interaction.guild.name} Application Failed.",color=0xFF0000)
      embed.add_field(name="Staff Name", value=member.mention)
      embed.add_field(name="Feedback", value=feedback)
      embed.add_field(name="Signed By", value=interaction.user.mention)
      await interaction.response.send_message("Result Sent", ephemeral=True)
      await channel.send(member.mention, embed=embed)

#keep_alive.keep_alive()
#my_secret = os.environ['TOKEN']
while True:
  bot.run("Your_Token_Here")