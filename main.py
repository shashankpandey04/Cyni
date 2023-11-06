import discord
from discord.ext import commands
import datetime
import traceback
import json
import sys
import logging
import os
import keep_alive

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!",intents=intents)

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
            "staff_roles": []
            # Add other default configuration keys as needed
        }
        update_server_config(guild_id, config)
    return config


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/support"))
    await bot.tree.sync()
    save_data()
    for guild in bot.guilds:
        create_or_get_server_config(guild.id)

def get_staff_roles(guild_id):
    """Get staff roles for a specific guild."""
    config = load_config()
    return config.get(str(guild_id), {}).get("staff_roles", [])

def get_support_role_id(guild_id):
    """Get support role ID for a specific guild."""
    config = get_server_config(guild_id)
    return config.get("support_role")

@bot.event
async def on_guild_join(guild):
    create_or_get_server_config()

@bot.command()
async def show_config(ctx):
    guild_id = ctx.guild.id
    config = get_server_config(guild_id)
    await ctx.send(f"Server Configuration: {config}")

@bot.command()
async def updateconfig(ctx, key, value):
    guild_id = ctx.guild.id
    config = get_server_config(guild_id)
    config[key] = value
    update_server_config(guild_id, config)
    await ctx.send(f"Configuration updated: {key} -> {value}")

@bot.tree.command()
async def support(interaction: discord.Interaction):
    '''Link to Support Server'''
    embed = discord.Embed(title="Need Assistance?",description=f"Join our Support Discord Server and our support team will help you with your problem. [Click Here](https://discord.gg/VVjJjgEaFk)",color=60407)
    await interaction.response.send_message(embed=embed)

@bot.tree.command()
async def staffroleadd(interaction: discord.Interaction, role: discord.Role):
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
        
        await interaction.response.send_message(f"Added {role.mention} as a staff role.")
    except commands.MissingPermissions:
        await interaction.response.send_message("You don't have permission to use this command.")
    except Exception as e:
        print(e)
        await interaction.response.send_message(f"Failed to add {role.mention} as a staff role.")

@bot.tree.command()
@commands.has_permissions(administrator=True)
async def staffroleremove(interaction: discord.Interaction, role: discord.Role):
    '''Remove Staff Role from server.'''
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

@bot.tree.command()
async def hello(interaction: discord.Interaction):
    '''Bot says Hello in chat.'''
    await interaction.response.send_message("Hello!")

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
        's': 1,  # seconds
        'm': 60,  # minutes
        'h': 3600  # hours
    }
    guild_id = interaction.guild.id
    staff_roles = get_staff_roles(guild_id)

    if not any(role.id in staff_roles for role in interaction.user.roles):
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
    if interaction.guild.me.top_role <= role:
        await interaction.response.send_message("Sorry, I don't have permission to add this role.")
    elif interaction.user.top_role <= role:
        await interaction.response.send_message("You can't add a role higher than you.")
    else:
        await member.add_roles(role)
        embed = discord.Embed(title='Role added.',description=f"Role {role.mention} add to {member.mention}",color=0x00FF00)
        await interaction.response.send_message(embed=embed)

@bot.tree.command()
async def roleremove(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    '''Removes a role from member'''
    if interaction.guild.me.top_role <= role:
        await interaction.response.send_message("Sorry, I don't have permission to remove this role.")
    elif interaction.user.top_role <= role:
        await interaction.response.send_message("You can't remove a role higher than you.")
    else:
        await member.remove_roles(role)
        embed = discord.Embed(title='Role Removed.',description=f"Role {role.mention} is now removed from {member.mention}",color=0xFF0000)
        await interaction.response.send_message(embed=embed)

@bot.tree.command()
async def kick(interaction: discord.Interaction, member: discord.Member, *, reason: str):
    '''Kicks user from server'''
    guild_id = interaction.guild.id
    staff_roles = get_staff_roles(guild_id)

    if not any(role.id in staff_roles for role in interaction.user.roles):
        embed = discord.Embed(title="Kick Denied", description="You don't have permission to use this command.", color=0xFF0000)
        await interaction.response.send_message(embed=embed)
        return

    if interaction.guild.me.top_role <= member.top_role:
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

    if not any(role.id in staff_roles for role in interaction.user.roles):
        embed = discord.Embed(title="Ban Denied", description="You don't have permission to use this command.", color=0xFF0000)
        await interaction.response.send_message(embed=embed)
        return

    if interaction.guild.me.top_role <= member.top_role:
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
async def warn(interaction: discord.Interaction, user: discord.User, *, reason: str):
    '''Log warning against user in server.'''
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    guild_id = str(interaction.guild.id)
    user_id = str(user.id)
    
    # Calculate the next case number without modifying existing data
    case_number = get_next_case_number(guild_id, user_id)
    
    staff_roles = get_staff_roles(guild_id)

    if not any(role.id in staff_roles for role in interaction.user.roles):
        embed = discord.Embed(title="Warn Denied", description="You don't have permission to use this command.", color=0xFF0000)
        await interaction.response.send_message(embed=embed)
        return

    if staff_roles:
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

    if not any(role.id in staff_roles for role in interaction.user.roles):
        embed = discord.Embed(title="Kick Denied", description="You don't have permission to use this command.", color=0xFF0000)
        await interaction.response.send_message(embed=embed)
        return
    if staff_roles:
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
        else:
            await interaction.response.send_message('❌ You do not have permission to use this command.')

@bot.tree.command()
async def membercount(interaction: discord.Interaction):
    '''Gives the total number of members in server.'''
    embed = discord.Embed(title="Members",description=f"{interaction.guild.name} got {interaction.guild.member_count} members as right now.",color=0x0F00FF)
    await interaction.response.send_message(embed=embed)
        
keep_alive.keep_alive()

#If Using Replit Secrets then use this code.
#bot_token = os.environ["Token Name"]
#Then replace the `"YOUR_BOT_TOKEN"` with `bot_token`
#Example: bot.run(bot_token)

bot.run("YOUR_BOT_TOKEN")
