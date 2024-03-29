import discord
from discord.ext import commands
import datetime
import requests
import sys
import traceback
import logging
from prefixcommand import prefix_warn
from utils import *
import random
from menu import *
from threading import Thread
#from hyme import run_staff_bot as run_hyme
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=':', intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
  print("Logged in into Discord")
  await bot.tree.sync()
  save_data()
  for guild in bot.guilds:
    create_or_get_server_config(guild.id)
  cleanup_guild_data(bot)
  await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/support | Cyni"))
  await bot.load_extension("jishaku")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)
    if message.content.startswith('?warn'):
        ctx = await bot.get_context(message)
        mentioned_users = message.mentions
        if mentioned_users:
            mentioned_user = mentioned_users[0]
            remaining_content = message.content[len('?warn'):].lstrip().lstrip(
                mentioned_user.mention).strip()
            if remaining_content:
                reason = remaining_content
                await prefix_warn(ctx, mentioned_user, reason=reason)
            else:
                await message.channel.send("You need to provide a reason when using ?warn.")
            
    guild_id = message.guild.id
    server_config = get_server_config(guild_id)
    anti_ping_enabled = server_config.get(str(guild_id), {}).get("anti_ping", "false").lower() == "true"
    if anti_ping_enabled == "false":
        return
    else:
      anti_ping_roles = server_config.get("anti_ping_roles", [])
      bypass_antiping_roles = server_config.get("bypass_antiping_roles", [])
      try:
        mentioned_user = message.mentions[0]
      except IndexError:
        return
      author_has_bypass_role = any(role.id in bypass_antiping_roles for role in message.author.roles)
      has_management_role = any(role.id in anti_ping_roles for role in mentioned_user.roles)
      has_administrator_permission = message.author.guild_permissions.administrator
      if author_has_bypass_role or has_administrator_permission:
          return
      elif has_management_role:
        author_can_warn = any(role.id in anti_ping_roles for role in message.author.roles)
        if not author_can_warn:
            warning_message = f"{message.author} Refrain from pinging users with Anti-ping enabled role, if it's not necessary."
            await message.channel.send(warning_message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound) and ctx.message.content.startswith('?warn'):
        return
    existing_uids = get_existing_uids()
    error_uid = generate_error_uid(existing_uids)
    sentry = discord.Embed(
        title="❌ An error occurred.",
        description=f"Error I'd `{error_uid}`\nThis can be solved by joining our support server.\n[Join Cyni Support](https://discord.gg/2D29TSfNW6)",
        color=0xFF0000
    )
    await ctx.send(embed=sentry)
    
    error_data = {
        "error_uid": error_uid,
        "command": ctx.message.content,
        "error": str(error),
        "traceback": ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    }
    
    log_error('cerror.json', error, error_uid)

existing_uids = get_existing_uids()

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    error_uid = generate_error_uid(existing_uids)
    logger.error(f"Error UID: {error_uid}\n{''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}")
sys.excepthook = handle_exception

@bot.event
async def on_guild_join(guild):
  create_or_get_server_config(guild.id)

@bot.tree.command()
async def say(interaction: discord.Interaction, message: str):
  '''Broadcasts a message in the channel'''
  channel = interaction.channel
  if await check_permissions(interaction, interaction.user):
    try:
        await interaction.response.send_message("Message sent.", ephemeral=True)
        await channel.send(message)
    except Exception as e:
        await on_general_error(interaction,e)
  else:
     await interaction.response.send_message("❌ You are not permitted to use this command",ephemeral=True)

@bot.tree.command()
async def slowmode(interaction: discord.Interaction, duration: str):
  '''Sets slowmode in channel'''
  time_units = {'s': 1, 'm': 60, 'h': 3600}
  try:
      if await check_permissions(interaction, interaction.user):
        try:
          amount = int(duration[:-1])
          unit = duration[-1]
          if unit not in time_units:
            raise ValueError
        except (ValueError, IndexError):
          await interaction.response.send_message('Invalid duration format. Please use a number followed by "s" for seconds, "m" for minutes, or "h" for hours.',ephemeral=True)
          return
        total_seconds = amount * time_units[unit]
        if total_seconds == 0:
          await interaction.response.send_message("Slow mode disabled from the channel.")
        elif total_seconds > 21600:
          await interaction.response.send_message('Slow mode duration cannot exceed 6 hours (21600 seconds).')
          return
        else:
          await interaction.channel.edit(slowmode_delay=total_seconds)
          await interaction.response.send_message(f'Slow mode set to {amount} {unit} in this channel.',ephemeral=True)
      else:
        await interaction.response.send_message("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_general_error(interaction, error)

@bot.tree.command()
async def ping(interaction: discord.Interaction):
  '''Check the bot's ping.'''
  latency = round(bot.latency * 1000)
  await interaction.response.send_message(f'Pong! Latency: {latency}ms')

@bot.tree.command()
async def roleadd(interaction: discord.Interaction, member: discord.Member,role: discord.Role):
  '''Add a role to member'''
  try:
      if await check_permissions(interaction, interaction.user):
        if not interaction.user.guild_permissions.manage_roles:
          await interaction.response.send_message("❌ You don't have the 'Manage Roles' permission.")
        elif role >= member.top_role:
          await interaction.response.send_message("❌ I can't add a role higher than or equal to the member's top role.")
        else:
          await member.add_roles(role)
          embed = discord.Embed(
              title='Role added.',
              description=f"Role {role.mention} added to {member.mention}",
              color=0x00FF00)
          await interaction.response.send_message(embed=embed)
      else:
        await interaction.response.send_message("❌ You don't have permission to use this command.")
  except Exception as error:
    await on_general_error(interaction, error)

@bot.tree.command()
async def roleremove(interaction: discord.Interaction, member: discord.Member,role: discord.Role):
  '''Removes a role from member'''
  try:
      if await check_permissions(interaction, interaction.user):
        if not interaction.user.guild_permissions.manage_roles:
          await interaction.response.send_message("❌ You don't have the 'Manage Roles' permission.")
        elif role >= member.top_role:
          await interaction.response.send_message("❌ I can't remove a role higher than or equal to the member's top role.")
        elif role>= bot.top_role:
           await interaction.response.send_message("❌ I can't give roles higher than me.")
        else:
          await member.remove_roles(role)
          embed = discord.Embed(title='Role Removed.',description=f"Role {role.mention} is now removed from {member.mention}",color=0xFF0000)
          await interaction.response.send_message(embed=embed)
      else:
        await interaction.response.send_message("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_general_error(interaction, error)

@bot.tree.command()
async def kick(interaction: discord.Interaction, member: discord.Member, *, reason: str):
  '''Kicks user from server'''
  guild_id = interaction.guild.id
  try:
      if await check_permissions(interaction, interaction.user):
        if interaction.guild.me.top_role <= member.top_role:
          embed = discord.Embed(title='Kick Failed',description="Sorry, I don't have permission to kick users higher than me.", color=0XFF0000)
          await interaction.response.send_message(embed=embed)
        elif interaction.user.top_role <= member.top_role:
          embed = discord.Embed(title="Kick Denied",description="You can't kick users with higher roles.",color=0xFF0000)
          await interaction.response.send_message(embed=embed)
        else:
          kick_embed = discord.Embed(title='User Kicked',description=f"User {member.mention} has been kicked for {reason}",color=0xFF0000,)
          kick_embed.set_footer(text=datetime.datetime.utcnow())
          try:
            await member.kick(reason=reason)
            await interaction.response.send_message(embed=kick_embed,ephemeral=True)
            mod_log_channel_id = modlogchannel(guild_id)
            if mod_log_channel_id is not None:
              mod_log_channel = interaction.guild.get_channel(mod_log_channel_id)
              if mod_log_channel:
                await mod_log_channel.send(embed=kick_embed)
            else:
              await interaction.channel.send("❌ Moderation log channel is not defined in the server configuration.")
          except discord.Forbidden:
            fail_embed = discord.Embed(title="Kick Failed", description=f"You can't kick {member.mention}.")
            await interaction.response.send_message(embed=fail_embed)
      else:
        embed = discord.Embed(title="Kick Denied",description="❌ You don't have permission to use this command.",color=0xFF0000)
        await interaction.response.send_message(embed=embed)
  except Exception as error:
          await on_general_error(interaction, error) 

@bot.tree.command()
async def ban(interaction: discord.Interaction, member: discord.Member, *,reason: str):
  '''Ban user from server'''
  guild_id = interaction.guild.id
  try:
    if await check_permissions(interaction, interaction.user):
      if interaction.guild.me.top_role <= member.top_role:
          embed = discord.Embed(title='Ban Failed',description="Sorry, I don't have permission to Ban users higher than me.",color=0XFF0000)
          await interaction.response.send_message(embed=embed)
      elif interaction.user.top_role <= member.top_role:
          embed = discord.Embed(title="Ban Denied",description="You can't Ban users with higher roles.",color=0xFF0000)
          await interaction.response.send_message(embed=embed)
      else:
          try:
            await member.ban(reason=reason)
            mod_log_channel_id = modlogchannel(guild_id)
            if mod_log_channel_id is not None:
              mod_log_channel = interaction.guild.get_channel(mod_log_channel_id)
              if mod_log_channel:
                ban_embed = discord.Embed(title='User Banned',description=f"User {member} got banned for {reason}",color=0xFF0000)
                ban_embed.set_footer(text=datetime.datetime.utcnow())
                await mod_log_channel.send(embed=ban_embed)
              else:
                await interaction.response.send_message("❌ Moderation log channel is not defined in the server configuration.")
            else:
              await interaction.response.send_message('❌ Moderation log channel is not defined in the server configuration.')
            success_embed = discord.Embed(title='User Banned',description=f"User {member} got banned for {reason}",color=0xFF0000)
            success_embed.set_footer(text=datetime.datetime.utcnow())
            await interaction.response.send_message(embed=success_embed,ephemeral=True)
          except discord.Forbidden:
            fail_embed = discord.Embed(title="Ban Failed", description=f"You can't Ban {member.mention}.")
            await interaction.response.send_message(embed=fail_embed)
    else:
        await interaction.response.send_message("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_general_error(interaction, error)

@bot.tree.command()
async def delwarn(interaction: discord.Interaction, user: discord.User,case_number: int):
  '''Delete a user warning.'''
  guild_id = interaction.guild.id
  try:
    if await check_permissions(interaction, interaction.user):
      mod_log_channel_id = modlogchannel(guild_id)
      if mod_log_channel_id is not None:
          mod_log_channel = interaction.guild.get_channel(mod_log_channel_id)
          if mod_log_channel:
            user_id = str(user.id)
            guild_id_str = str(guild_id)
            if guild_id_str in warnings and user_id in warnings[guild_id_str]:
              user_warnings = warnings[guild_id_str][user_id]
              for warning in user_warnings:
                if warning['case_number'] == case_number:
                  user_warnings.remove(warning)
                  for i, warning in enumerate(user_warnings):
                    warning['case_number'] = i + 1
                  save_data()
                  log_embed = discord.Embed(title="Moderation Warning Revoked",color=0x00FF00)
                  log_embed.add_field(name="Case Number", value=str(case_number))
                  log_embed.add_field(name="User", value=user.mention)
                  log_embed.add_field(name="Action", value="Delete Warning")
                  log_embed.add_field(name="Moderator",value=interaction.user.mention)
                  log_embed.add_field(name="Date",value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                  await mod_log_channel.send(embed=log_embed)
                  embed = discord.Embed(title="User warning removed.",description=f"Warning number {case_number} removed from {user.mention}.",color=0x0000FF)
                  await interaction.response.send_message(embed=embed,ephemeral=True)
                  return
              embed = discord.Embed(title="Case not found.", description=f'Warning case #{case_number} not found for {user.mention}.', color=0xFF0000)
              await interaction.response.send_message(embed=embed)
            else:
              await interaction.response.send_message(f'{user.mention} does not have any warnings.')
          else:
            await interaction.channel.send("❌ Moderation log channel is not defined in the server configuration.")
      else:
          await interaction.response.send_message("❌ Moderation log channel is not defined in the server configuration.")
    else:
      await interaction.response.send_message("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_general_error(interaction, error)


@bot.tree.command()
async def warnlog(interaction: discord.Interaction, user: discord.User):
  """View all warnings of a user in the guild."""
  guild_id = str(interaction.guild.id)
  user_id = str(user.id)
  try:
      if guild_id in warnings and user_id in warnings[guild_id]:
        user_warnings = warnings[guild_id][user_id]
        if user_warnings:
          embed = discord.Embed(title=f"Warnings for {user.name}#{user.discriminator}",color=discord.Color.red())
          for warning in user_warnings:
            embed.add_field(name=f"Case #{warning['case_number']}",value=f"**Reason:** {warning['reason']}\n**Date:** {warning['date']}",inline=False)
          await interaction.response.send_message(embed=embed,ephemeral=True)
        else:
          await interaction.response.send_message(f"{user.name}#{user.discriminator} has no warnings.",ephemeral=True)
      else:
        await interaction.response.send_message(f"No warnings found for {user.name}#{user.discriminator} in this guild.",ephemeral=True)
  except Exception as error:
            await on_general_error(interaction, error)

@bot.tree.command()
async def warn(interaction: discord.Interaction, user: discord.User, *,reason: str):
  '''Log a warning against a user in the server.'''
  try:
      current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      guild_id = str(interaction.guild.id)
      user_id = str(user.id)
      if await check_permissions(interaction, interaction.user):
        mod_log_channel_id = modlogchannel(guild_id)
        if mod_log_channel_id is not None:
          mod_log_channel = interaction.guild.get_channel(mod_log_channel_id)
          if mod_log_channel:
            if guild_id not in warnings:
              warnings[guild_id] = {}
            if user_id not in warnings[guild_id]:
              warnings[guild_id][user_id] = []
            case_number = get_next_case_number(guild_id, user_id)
            warnings[guild_id][user_id].append({'case_number': case_number,'reason': reason,'date': current_datetime})
            save_data()
            await interaction.response.send_message(f"✅ {user} got warned for {reason}\nCase: {case_number}")
            log_embed = discord.Embed(title="Moderation Log", color=0xFF0000)
            log_embed.add_field(name="Case Number", value=str(case_number))
            log_embed.add_field(name="User", value=user.mention)
            log_embed.add_field(name="Action", value="Warn")
            log_embed.add_field(name="Reason", value=reason)
            log_embed.add_field(name="Moderator", value=interaction.user.mention)
            log_embed.add_field(name="Date", value=current_datetime)
            await mod_log_channel.send(embed=log_embed)
          else:
            await interaction.channel.send("❌ Moderation log channel is not defined in the server configuration.")
        else:
          await interaction.response.send_message('❌ Moderation log channel is not defined in the server configuration.')
      else:
        await interaction.response.send_message( "❌ You don't have permission to use this command.")
  except Exception as error:
          await on_general_error(interaction, error)

@bot.tree.command()
async def membercount(interaction: discord.Interaction):
  '''Gives the total number of members in server.'''
  await interaction.response.send_message(f"{interaction.guild.member_count} members.")

@bot.command()
async def membercount(interaction: discord.Interaction):
  await interaction.channel.send(f"{interaction.guild.member_count} members.")

@bot.tree.command()
async def promote(interaction: discord.Interaction, member: discord.Member, *,old_rank: discord.Role, next_rank: discord.Role,approved: discord.Role, reason: str):
  '''Promote Server Staff'''
  guild_id = interaction.guild.id
  management_roles = get_management_roles(guild_id)
  is_management = any(role.id in management_roles for role in interaction.user.roles)
  is_admin = interaction.user.guild_permissions.administrator
  try:
      if await check_permissions_management(interaction, interaction.user):
        channel = interaction.channel
        embed = discord.Embed(title=f"{interaction.guild.name} Promotions.",color=0x00FF00)
        embed.add_field(name="Staff Name", value=member.mention)
        embed.add_field(name="Old Rank", value=old_rank.mention)
        embed.add_field(name="New Rank", value=next_rank.mention)
        embed.add_field(name="Approved By", value=approved.mention)
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Signed By", value=interaction.user.mention)
        await interaction.response.send_message("Promotion Sent", ephemeral=True)
        await channel.send(member.mention, embed=embed)
      else:
        await interaction.response.send_message("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_general_error(interaction, error)

@bot.tree.command()
async def demote(interaction: discord.Interaction, member: discord.Member, *,old_rank: discord.Role, next_rank: discord.Role,approved: discord.Role, reason: str):
  '''Demote Server Staff'''
  try:
      if await check_permissions_management(interaction, interaction.user):
        channel = interaction.channel
        embed = discord.Embed(title=f"{interaction.guild.name} Demotions.",color=0x00FF00)
        embed.add_field(name="Staff Name", value=member.mention)
        embed.add_field(name="Old Rank", value=old_rank.mention)
        embed.add_field(name="New Rank", value=next_rank.mention)
        embed.add_field(name="Approved By", value=approved.mention)
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Signed By", value=interaction.user.mention)
        await interaction.response.send_message("Demotion Sent", ephemeral=True)
        await channel.send(member.mention, embed=embed)
      else:
        await interaction.response.send_message("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_general_error(interaction, error)

@bot.tree.command()
async def passapp(interaction: discord.Interaction, member: discord.Member, *,server_message: str, feedback: str):
  '''Post Passed Application Result'''
  try:
      if await check_permissions_management(interaction, interaction.user):
        channel = interaction.channel
        embed = discord.Embed(
        title=f"{interaction.guild.name} Application Passed.", color=0x00FF00)
        embed.add_field(name="Staff Name", value=member.mention)
        embed.add_field(name="Server Message", value=server_message)
        embed.add_field(name="Feedback", value=feedback)
        embed.add_field(name="Signed By", value=interaction.user.mention)
        await interaction.response.send_message("Result Sent", ephemeral=True)
        await channel.send(member.mention, embed=embed)
      else:
        await interaction.response.send_message("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_general_error(interaction, error)

@bot.tree.command()
async def failapp(interaction: discord.Interaction, member: discord.Member, *,feedback: str):
  '''Post Failed Application result.'''
  try:
      if await check_permissions_management(interaction, interaction.user):
          channel = interaction.channel
          embed = discord.Embed(
          title=f"{interaction.guild.name} Application Failed.", color=0xFF0000)
          embed.add_field(name="Staff Name", value=member.mention)
          embed.add_field(name="Feedback", value=feedback)
          embed.add_field(name="Signed By", value=interaction.user.mention)
          await interaction.response.send_message("Result Sent", ephemeral=True)
          await channel.send(member.mention, embed=embed)
      else:
          await interaction.response.send_message("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_general_error(interaction, error)

@bot.tree.command()
async def purge(interaction: discord.Interaction, amount: int):   
  '''Purge messages from channel'''
  try:
    if await check_permissions(interaction, interaction.user):
      await interaction.response.send_message(f'Cleared {amount} messages.',ephemeral=True)
      await interaction.channel.purge(limit=amount + 1)      
    else:
      await interaction.response.send_message("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_general_error(interaction, error)

@bot.tree.command()
async def custom_run(interaction:discord.Interaction,command_name:str):
    '''Run Custom Command'''
    if await check_permissions(interaction, interaction.user):
          await run_custom_command(interaction, command_name)
          embed = discord.Embed(title="Custom Command Executed",description=f"Custom Command {command_name} executed by {interaction.user.mention}",color=0x00FF00)
          await interaction.response.send_message(embed=embed)
    else:
      await interaction.response.send_message("❌ You don't have permission to use this command.")

@bot.tree.command()
async def custom_manage(interaction:discord.Interaction, action:str, name:str):
    '''Manage Custom Commands (create, delete, list)'''
    try:
      if await check_permissions_management(interaction, interaction.user):
            if action == 'create':
                await create_custom_command(interaction, name) 
            elif action == 'delete':
                await delete_custom_command(interaction, name)
            elif action == 'list':
                await list_custom_commands(interaction)
            else:
                await interaction.response.send_message("Invalid action. Valid actions are: create, delete, list.")
            await interaction.response.send_message("Custom command executed successfully.")
    except Exception as error:
          await on_general_error(interaction, error)

def list_custom_commands_embeds(interaction):
    config = load_customcommand()
    guild_id = str(interaction.guild.id)
    custom_commands = config.get(guild_id, {})
    if not custom_commands:
        return [discord.Embed(description="No custom commands found for this server.")]
    embeds = []
    for name, details in custom_commands.items():
        embed = discord.Embed(title=details.get('title', ''),description=details.get('description', ''), color=details.get('colour', discord.Color.default().value))
        image_url = details.get('image_url')
        if image_url:
            embed.set_image(url=image_url)
        embeds.append(embed)
    return embeds

async def list_custom_commands(interaction):
    embeds = list_custom_commands_embeds(interaction)
    for embed in embeds:
        await interaction.channel.send(embed=embed)

async def run_custom_command(interaction, command_name):
    config = load_customcommand()
    guild_id = str(interaction.guild.id)
    command_details = config.get(guild_id, {}).get(command_name)
    if command_details:
        embed = discord.Embed(
            title=command_details.get('title', ''),
            description=command_details.get('description', ''),
            color=command_details.get('colour', discord.Color.default().value))
        image_url = command_details.get('image_url')
        embed.set_footer(text="Executed By: " + interaction.user.name)
        if image_url:
            embed.set_image(url=image_url)
        channel_id = command_details.get('channel')
        channel = bot.get_channel(channel_id)
        role_id = command_details.get('role')
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role:
                await channel.send(f"<@&{role_id}>")  
            else:
                await interaction.channel.send("Role not found. Please make sure the role exists.")
                return
        await channel.send(embed=embed)
        await interaction.channel.send(f"Custom command '{command_name}' executed in {channel.mention}.")
    else:
        await interaction.channel.send(f"Custom command '{command_name}' not found.")

async def create_custom_command(interaction, command_name):
    config = load_customcommand()
    guild_id = str(interaction.guild.id)
    if command_name in config.get(guild_id, {}):
        await interaction.channel.send(f"Custom command '{command_name}' already exists.")
        return
    if len(config.get(guild_id, {})) >= 5:
        await interaction.channel.send("Sorry, the server has reached the maximum limit of custom commands (5).")
        return
    await interaction.channel.send("Enter embed title:")
    title = await bot.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
    await interaction.channel.send("Enter embed description:")
    description = await bot.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
    await interaction.channel.send("Enter embed colour (hex format, e.g., #RRGGBB):")
    colour = await bot.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
    await interaction.channel.send("Enter image URL (enter 'none' for no image):")
    image_url_input = await bot.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
    await interaction.channel.send("Enter default channel to post message (mention the channel):")
    channel_input = await bot.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
    await interaction.channel.send("Enter role ID to ping (enter 'none' for no role):")
    role_id_input = await bot.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
    channel_id = int(channel_input.content[2:-1])
    if role_id_input.content.lower() == 'none':
        role_id = None
    else:
        role_id = int(role_id_input.content)
    try:
        color_decimal = int(colour.content[1:], 16)
    except ValueError:
        await interaction.channel.send("Invalid hex color format. Please use the format #RRGGBB.")
        return
    image_url = image_url_input.content.strip()
    if image_url.lower() == 'none':
        image_url = None
    if len(config.get(guild_id, {})) >= 5:
        await interaction.channel.send("Sorry, the server has reached the maximum limit of custom commands (5).")
        return
    config.setdefault(guild_id, {})[command_name] = {
        'title': title.content,
        'description': description.content,
        'colour': color_decimal,
        'channel': channel_id,
        'role': role_id,
        'image_url': image_url,
    }
    save_customcommand(config)
    embed = discord.Embed(title="Custom Command Created", description=f"Custom command '{command_name}' created successfully.", color=discord.Color.random())
    await interaction.channel.send(embed=embed)

async def delete_custom_command(interaction, command_name):
  config = load_customcommand()
  guild_id = str(interaction.guild.id)
  command_details = config.get(guild_id, {}).get(command_name)
  if command_details:
    del config[guild_id][command_name]
    save_customcommand(config)
    await interaction.channel.send(f"Custom command '{command_name}' deleted successfully.")
  else:
    await interaction.channel.send(f"Custom command '{command_name}' not found.")

@bot.tree.command()
async def pick(interaction: discord.Interaction, option1:str, option2:str):
  '''Pick between two options'''
  option = random.choice([option1, option2])
  await interaction.response.send_message(f"I pick {option}")

@bot.command(name='pick')
async def pick(ctx, option1, option2):
  option = random.choice([option1, option2])
  await ctx.send(f"I pick {option}")

@bot.tree.command()
async def catimage(interaction:discord.Interaction):
  '''Get Random Cat Image'''
  response = requests.get("https://api.thecatapi.com/v1/images/search")
  data = response.json()
  image_url = data[0]["url"]
  embed = discord.Embed(title="Random Cat Image", color=discord.Color.random())
  embed.set_image(url=image_url)
  await interaction.response.send_message(embed=embed)
  

@bot.tree.command()
async def dogimage(interaction: discord.Interaction):
    '''Get Random Dog Image'''
    response = requests.get("https://api.thedogapi.com/v1/images/search")
    data = response.json()
    image_url = data[0]["url"]
    embed = discord.Embed(title="Random Dog Image", color=discord.Color.random())
    embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command()
async def getavatar(interaction: discord.Interaction, user: discord.User):
  '''Get any user avatar from server'''
  try:
    embed = discord.Embed(title=f"{user.name}'s Profile Photo", color=0x00FFFF)
    embed.set_image(url=user.avatar)
    await interaction.response.send_message(embed=embed)
  except Exception as error:
        await on_general_error(interaction, error)

@bot.event
async def on_general_error(ctx, error):
    file_path = 'cerror.json'
    existing_uids = get_existing_uids(file_path)
    error_uid = generate_error_uid(existing_uids)
    log_error(file_path, error, error_uid)
    
    if isinstance(ctx, discord.Interaction):
        embed = discord.Embed(
            title="❌ An error occurred",
            description=f"An error occurred (Error UID: `{error_uid}`). Please contact support.",
            color=0xFF0000
        )
        await ctx.channel.send(embed=embed)
    else:
        await ctx.channel.send(f"An error occurred (Error UID: `{error_uid}`). Please contact support.")

@bot.command(name='whois')
async def whois(ctx, *, user_info=None):
    guild_id = str(ctx.guild.id)
    server_config = get_server_config(guild_id)
    if user_info is None:
          member = ctx.author
    else:
          if user_info.startswith('<@') and user_info.endswith('>'):
              user_id = int(user_info[2:-1])
              member = ctx.guild.get_member(user_id)
          else:
              member = discord.utils.find(lambda m: m.name == user_info, ctx.guild.members)
    if member:
          support_server_id = 1152949579407442050
          support_server = bot.get_guild(support_server_id)
          user_emoji = discord.utils.get(support_server.emojis, id=1191057214727786598)
          cyni_emoji = discord.utils.get(support_server.emojis, id=1185563043015446558)
          discord_emoji = discord.utils.get(support_server.emojis, id=1191057244004044890)
          with open('staff.json', 'r') as file:
              staff_data = json.load(file)
          embed = discord.Embed(title="User Information", color=member.color)
          hypesquad_flags = member.public_flags
          hypesquad_values = [str(flag).replace("UserFlags.", "").replace("_", " ").title() for flag in hypesquad_flags.all()]
          if hypesquad_values:
              hypesquad_text = "\n".join(hypesquad_values)
              embed.add_field(name=f"{discord_emoji} Discord Flags", value=f"{hypesquad_text}", inline=True)
          user_flags = staff_data.get(member.name, "").replace("{cyni_emoji}", "")
          user_flags = [flag.strip() for flag in user_flags.split("\n") if flag.strip()]
          if user_flags:
              staff_text = "\n".join(user_flags)
              embed.add_field(name=f'{cyni_emoji} Staff Flags', value=f" {staff_text}", inline=True)
          embed.set_thumbnail(url=member.avatar.url)
          embed.add_field(name=f"{user_emoji} Username", value=member.name, inline=True)
          embed.add_field(name="User ID", value=member.id, inline=True)
          embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
          embed.add_field(name="Joined Discord", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
          if member.guild_permissions.administrator:
              embed.add_field(name="Role", value="Administrator", inline=True)
          elif member.guild_permissions.manage_messages:
              embed.add_field(name="Role", value="Moderator", inline=True)
          else:
              embed.add_field(name="Role", value="Member", inline=True)
          embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
          await ctx.send(embed=embed)
    else:
          await ctx.send("User not found.")

'''
@bot.tree.command()
async def serverinfo(interaction:discord.Interaction):
    try:
      server = interaction.guild
      name = server.name
      owner = server.owner
      created = server.created_at.strftime("%Y-%m-%d %H:%M:%S")
      bot_joined = server.me.joined_at.strftime("%Y-%m-%d %H:%M:%S")
      notifications = server.default_notifications.name
      members = server.member_count
      nitro_boosts = server.premium_subscription_count
      two_factor_auth = server.mfa_level
      verification_level = server.verification_level.name
      explicit_content_filter = server.explicit_content_filter.name
      member_verification_gate = server.mfa_level
      category_channels = sum(1 for channel in server.channels if isinstance(channel, discord.CategoryChannel))
      text_channels = sum(1 for channel in server.channels if isinstance(channel, discord.TextChannel))
      voice_channels = sum(1 for channel in server.channels if isinstance(channel, discord.VoiceChannel))
      announcement_channels = sum(1 for channel in server.channels if isinstance(channel, discord.TextChannel) and channel.is_news())
      embed = discord.Embed(title="Server Information", color=discord.Color.blue())
      embed.add_field(name="Name", value=name, inline=False)
      embed.add_field(name="Owner", value=owner, inline=False)
      embed.add_field(name="Created", value=created, inline=False)
      embed.add_field(name="Bot Joined", value=bot_joined, inline=False)
      embed.add_field(name="Notifications", value=notifications, inline=False)
      embed.add_field(name="Members", value=members, inline=False)
      embed.add_field(name="Nitro Boosts", value=nitro_boosts, inline=False)
      embed.add_field(name="2FA Settings", value=two_factor_auth, inline=False)
      embed.add_field(name="Verification Level", value=verification_level, inline=False)
      embed.add_field(name="Explicit Content Filter", value=explicit_content_filter, inline=False)
      embed.add_field(name="Member Verification Gate", value=member_verification_gate, inline=False)
      embed.add_field(name="Category", value=category_channels, inline=False)
      embed.add_field(name="Text", value=text_channels, inline=False)
      embed.add_field(name="Voice/Stage", value=voice_channels, inline=False)
      embed.add_field(name="Announcement", value=announcement_channels, inline=False)
      embed.add_field(name="ID", value=server.id, inline=False)
      await interaction.response.send_message(embed=embed)
    except Exception as error:
          await on_general_error(interaction, error)
'''
@bot.tree.command()
async def support(interaction:discord.Interaction):
  '''Join Cyni Support Server'''
  embed = discord.Embed(title="Cyni Support Server",description="Need any help?\nJoin Cyni Support Server.",color=0x00FF00)
  await interaction.response.send_message(embed=embed ,view=SupportBtn())

@bot.command()
async def support(interaction:discord.Interaction):
  '''Join Cyni Support Server'''
  embed = discord.Embed(title="Cyni Support Server",description="Need any help?\nJoin Cyni Support Server.",color=0x00FF00)
  await interaction.channel.send(embed=embed ,view=SupportBtn())

@bot.tree.command()
async def servermanage(interaction:discord.Interaction):
  '''Manage Your Server with Cyni'''
  try:
    if interaction.user.guild_permissions.administrator:
      embed = discord.Embed(title="Server Manage",description='''
                          **Staff Roles:**
                          - *Discord Staff Roles:* These roles grant permission to use Cyni's moderation commands.\n
                          - *Management Roles:* Users with these roles can utilize Cyni's management commands, including Application Result commands, Staff Promo/Demo command, and setting the Moderation Log channel.

                          **Mod Logger:**
                          - *Moderation Log Channel:* This channel is designated for Cyni to log all moderation actions taken on the server.

                          **Server Config:**
                          - Easily view and edit your server configuration settings.

                          **Anti-ping Module:**
                          - Messages are sent if a user with specific roles attempts to ping anyone. Bypass roles can be configured to allow certain users to ping others with that role.

                          **Support Server:**
                          - Need assistance? Join the Cyni Support Server for help.
                            '''
                            ,color=0x00FF00) 
      await interaction.response.send_message(embed=embed, view=SetupView(),ephemeral=True)
    else:
      await interaction.response.send_message("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_general_error(interaction, error)

@bot.tree.command()
async def blocksearch(interaction:discord.Interaction, keyword: str):
  """Add blocked words from Cyni Search in server."""
  if await check_permissions_management(interaction, interaction.user):
    embed = discord.Embed(title="Blocked Search",description=f"**Keyword:** {keyword}\n**Blocked By:** {interaction.user.mention}",color=0x00FF00)
    await interaction.response.send_message("Blocked Search Added", ephemeral=True)
    with open("server_config.json", "r") as file:
        server_config = json.load(file)
        guild_id = str(interaction.guild.id)
        server_config[guild_id]["blocked_search"].append(keyword)
    with open("server_config.json", "w") as file:
        json.dump(server_config, file, indent=4)     
    await interaction.response.send_message(embed=embed)
  else:
    await interaction.response.send_message("❌ You don't have permission to use this command.")

@bot.tree.command()
async def websearch(interaction:discord.Interaction, topic: str):
  """Search on web using CYNI Search API"""
  guild_id = str(interaction.guild.id)
  server_config = get_server_config(guild_id)
  blocked_search = server_config.get('blocked_search', [])
  if topic in blocked_search:
      await interaction.response.send_message("Blocked word found in search query.")
      return
  result = search_api(topic)
  await interaction.response.send_message(f"{result}....")

@bot.tree.command()
async def birdimage(interaction: discord.Interaction):
    '''Get Random Bird Image'''
    response = requests.get("https://birbapi.astrobirb.dev/birb")
    data = response.json()
    image_url = data["image_url"]
    embed = discord.Embed(title="Random Bird Image", color=discord.Color.random())
    embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command()
async def joke(interaction:discord.Interaction):
   joke = fetch_random_joke()
   await interaction.response.send_message(joke)

@bot.command()
async def joke(ctx):
   joke = fetch_random_joke()
   await ctx.channel.send(joke)

def run_cynibot():
   bot.run("BOT_TOKEN")

def run_bots():
    bot_thread = Thread(target=run_cynibot)
    #staff_bot_thread = Thread(target=run_hyme)
    bot_thread.start()
    #staff_bot_thread.start()
    bot_thread.join()
    #staff_bot_thread.join()

run_bots()