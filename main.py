import discord
from discord.ext import commands
import datetime
import json
import requests
import sys
import traceback
import logging
from prefixcommand import prefix_warn
from utils import *
import random
from PIL import Image
from io import BytesIO
import uuid

premium_message = "✨ This server have premium enabled please use <@1168414327011823627> to use this command."


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

intents = discord.Intents.all()
bot = commands.AutoShardedBot(command_prefix=":", intents=intents)
dev_username = ['itsme.tony', 'long_winer12', 'imlimiteds']
staff_username = ['tearispro']


@bot.event
async def on_ready():
  print(f"Logged in as {bot.user} (ID: {bot.user.id})")
  await bot.tree.sync()
  save_data()
  for guild in bot.guilds:
    create_or_get_server_config(guild.id)
  await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/help | Cyni Systems"))
  await bot.load_extension("jishaku")


@bot.event
async def on_message(message):
  if message.author.bot:
    return

  await bot.process_commands(message)

  if message.content.startswith(':warn'):
    ctx = await bot.get_context(message)
    mentioned_users = message.mentions
    if mentioned_users:
      mentioned_user = mentioned_users[0]
      remaining_content = message.content[len(':warn'):].lstrip().lstrip(
          mentioned_user.mention).strip()
      if remaining_content:
        reason = remaining_content
        await prefix_warn(ctx, mentioned_user, reason=reason)
      else:
        await message.channel.send("You need to provide a reason when using ?warn.")

@bot.event
async def on_command_error(ctx, error):
  if isinstance(error,commands.CommandNotFound) and ctx.message.content.startswith(':warn'):
    return
  error_uid = "ERR" + str(hash(ctx.message.created_at))
  sentry = discord.Embed(title="Error",description=f"Error UID: {error_uid}\nThis can be solved by joining our support server. [Join Cyni Support](https://discord.gg/2D29TSfNW6)",color=0xFF0000)
  await ctx.send(embed=sentry)
  error_data = {"error_uid":error_uid, "command":ctx.message.content,"error":str(error),"traceback":''.join(traceback.format_exception(type(error), error, error.__traceback__))}

  with open('error.json', 'a') as json_file:
    json.dump(error_data, json_file)
    json_file.write('\n')


def handle_exception(exc_type, exc_value, exc_traceback):
  if issubclass(exc_type, KeyboardInterrupt):
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
    return
  error_uid = "ERR" + str(hash(exc_value))
  logger.error(f"Error UID: {error_uid}\n{''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}")
sys.excepthook = handle_exception

@bot.event
async def on_guild_join(guild):
  create_or_get_server_config(guild.id)

@bot.tree.command()
async def help(interaction: discord.Interaction):
  '''Link to Support Server'''
  embed = discord.Embed(
      title="Need Assistance?",
      description=
      f"Join our Support Discord Server and our support team will help you with your problem. [Click Here](https://discord.gg/2D29TSfNW6) ",
      color=60407)
  await interaction.response.send_message(embed=embed)

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
      embed = discord.Embed(
          title="Server Config Changed",
          description=f"Added {role.mention} as a staff role.",
          color=0x0000FF)
      await interaction.response.send_message(embed=embed)
    except:
      await interaction.response.send_message("Some Internal Error occured.")
  else:
    await interaction.response.send_message(
        "❌ You don't have permission to use this command.")

@bot.tree.command()
@commands.has_permissions(administrator=True)
async def managementadd(interaction: discord.Interaction, role: discord.Role):
  '''Add a Management role to the server configuration'''
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
        embed = discord.Embed(
            title="Server Config Changed",
            description=f"Added {role.mention} as a Management role.",
            color=0x0000FF)
        await interaction.response.send_message(embed=embed)
      else:
        embed = discord.Embed(
            title="Server Config Unchanged",
            description=f"{role.mention} is already a Management role.",
            color=0xFF0000)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
      await on_general_error(interaction, e)
  else:
    await interaction.response.send_message("❌ You don't have permission to use this command.")

@bot.tree.command()
@commands.has_permissions(administrator=True)
async def staffroleremove(interaction: discord.Interaction,role: discord.Role):
  '''Remove Staff Role from server.'''
  manegement_roles = get_management_roles(interaction.guild.id)
  if any(role.id in manegement_roles for role in interaction.user.roles) or (
      interaction.user.guild_permissions.administrator == True):
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
        await interaction.response.send_message(
            f"Removed {role.mention} from staff roles.")
      else:
        await interaction.response.send_message(
            f"{role.mention} is not in the staff roles list.")
    except Exception as e:
      print(e)
      await interaction.response.send_message(f"Failed to remove {role.mention} from staff roles.")
  else:
    await interaction.response.send_message("❌ You don't have permission to use this command.")

@bot.tree.command()
@commands.has_permissions(administrator=True)
async def managementremove(interaction: discord.Interaction,role: discord.Role):
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
        embed = discord.Embed(
            title="Server Config Error",
            description=f"{role.mention} is not in the staff roles list.")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
      print(e)
      await interaction.response.send_message("Some Internal Error occured.")
  else:
    await interaction.response.send_message(
        "❌ You don't have permission to use this command.")

@bot.tree.command()
async def say(interaction: discord.Interaction, message: str):
  '''Broadcasts a message in the channel'''
  channel = interaction.channel
  try:
    await interaction.response.send_message("Message sent.", ephemeral=True)
    await channel.send(message)
  except:
    await channel.send('Failed to process command.')

@bot.tree.command()
async def slowmode(interaction: discord.Interaction, duration: str):
  time_units = {'s': 1, 'm': 60, 'h': 3600}
  guild_id = interaction.guild.id
  management_role = get_management_roles(guild_id)
  staff_roles = get_staff_roles(guild_id)
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    try:
      if any(role.id in management_role for role in interaction.user.roles) or any(role.id in staff_roles for role in interaction.user.roles) or interaction.user.guild_permissions.administrator:
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
      else:
        await interaction.response.send_message("❌ You don't have permission to use this command.")
    except Exception as error:
          await on_general_error(interaction, error)
  else:
    await interaction.response.send_message(premium_message)

@bot.tree.command()
async def ping(interaction: discord.Interaction):
  '''Check the bot's ping.'''
  latency = round(bot.latency * 1000)
  await interaction.response.send_message(f'Pong! Latency: {latency}ms')

@bot.tree.command()
async def roleadd(interaction: discord.Interaction, member: discord.Member,role: discord.Role):
  '''Add a role to member'''
  guild_id = interaction.guild.id
  staff_roles = get_staff_roles(guild_id)
  management_roles = get_management_roles(guild_id)
  is_staff = any(role.id in staff_roles for role in interaction.user.roles)
  is_management = any(role.id in management_roles for role in interaction.user.roles)
  is_admin = interaction.user.guild_permissions.administrator
  try:
    server_config = get_server_config(guild_id)
    premium_status = server_config.get("premium", [])
    if 'false' in premium_status:
      if is_staff == True or is_management == True or is_admin== True :
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
    else:
      await interaction.response.send_message(premium_message)
  except Exception as error:
    await on_general_error(interaction, error)

@bot.tree.command()
async def roleremove(interaction: discord.Interaction, member: discord.Member,role: discord.Role):
  '''Removes a role from member'''
  guild_id = interaction.guild.id
  staff_roles = get_staff_roles(guild_id)
  management_roles = get_management_roles(guild_id)
  is_staff = any(role.id in staff_roles for role in interaction.user.roles)
  is_management = any(role.id in management_roles for role in interaction.user.roles)
  is_admin = interaction.user.guild_permissions.administrator
  try:
    server_config = get_server_config(guild_id)
    premium_status = server_config.get("premium", [])
    if 'false' in premium_status:
      if is_staff == True or is_management == True or is_admin == True:
        if not interaction.user.guild_permissions.manage_roles:
          await interaction.response.send_message("❌ You don't have the 'Manage Roles' permission.")
        elif role >= member.top_role:
          await interaction.response.send_message("❌ I can't remove a role higher than or equal to the member's top role.")
        else:
          await member.remove_roles(role)
          embed = discord.Embed(title='Role Removed.',description=f"Role {role.mention} is now removed from {member.mention}",color=0xFF0000)
          await interaction.response.send_message(embed=embed)
      else:
        await interaction.response.send_message("❌ You don't have permission to use this command.")
    else:
      await interaction.response.send_message(premium_message)
  except Exception as error:
          await on_general_error(interaction, error)

@bot.tree.command()
async def kick(interaction: discord.Interaction, member: discord.Member, *, reason: str):
  '''Kicks user from server'''
  guild_id = interaction.guild.id
  staff_roles = get_staff_roles(guild_id)
  management_roles = get_management_roles(guild_id)
  try:
    server_config = get_server_config(guild_id)
    premium_status = server_config.get("premium", [])
    if 'false' in premium_status:
      if any(role.id in staff_roles for role in interaction.user.roles) or any(role.id in management_roles for role in interaction.user.roles
      ) or interaction.user.guild_permissions.administrator:
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
            await interaction.response.send_message(embed=kick_embed)
            mod_log_channel_id = modlogchannel(guild_id)
            if mod_log_channel_id is not None:
              mod_log_channel = interaction.guild.get_channel(mod_log_channel_id)
              if mod_log_channel:
                await mod_log_channel.send(embed=kick_embed)
            else:
              await interaction.channel.send("❌ Moderation log channel is not defined in the server configuration.")
          except discord.Forbidden:
            fail_embed = discord.Embed(
                title="Kick Failed", description=f"You can't kick {member.mention}.")
            await interaction.response.send_message(embed=fail_embed)
      else:
        embed = discord.Embed(title="Kick Denied",description="❌ You don't have permission to use this command.",color=0xFF0000)
        await interaction.response.send_message(embed=embed)
    else:
      await interaction.response.send_message(premium_message)
  except Exception as error:
          await on_general_error(interaction, error) 

@bot.tree.command()
async def ban(interaction: discord.Interaction, member: discord.Member, *,reason: str):
  '''Ban user from server'''
  guild_id = str(interaction.guild.id)
  staff_roles = get_staff_roles(guild_id)
  management_roles = get_management_roles(guild_id)
  try:
    server_config = get_server_config(guild_id)
    premium_status = server_config.get("premium", [])
    if 'false' in premium_status:
      if any(role.id in staff_roles for role in interaction.user.roles) or any(role.id in management_roles for role in interaction.user.roles) or (interaction.user.guild_permissions.administrator == True):
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
            await interaction.response.send_message(embed=success_embed)
          except discord.Forbidden:
            fail_embed = discord.Embed(title="Ban Failed", description=f"You can't Ban {member.mention}.")
            await interaction.response.send_message(embed=fail_embed)
      else:
        await interaction.response.send_message("❌ You don't have permission to use this command.")
    else:
      await interaction.response.send_message(premium_message)
  except Exception as error:
          await on_general_error(interaction, error)

@bot.tree.command()
async def delwarn(interaction: discord.Interaction, user: discord.User,case_number: int):
  '''Delete a user warning.'''
  guild_id = interaction.guild.id
  staff_roles = get_staff_roles(guild_id)
  management_roles = get_management_roles(guild_id)
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    try:
      if any(role.id in staff_roles for role in interaction.user.roles) or any(role.id in management_roles for role in interaction.user.roles) or interaction.user.guild_permissions.administrator:
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
                  await interaction.response.send_message(embed=embed)
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
  else:
    await interaction.response.send_message(premium_message)


@bot.tree.command()
async def warnlog(interaction: discord.Interaction, user: discord.User):
  """View all warnings of a user in the guild."""
  guild_id=interaction.guild.id
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    guild_id = str(interaction.guild.id)
    user_id = str(user.id)
    try:
      if guild_id in warnings and user_id in warnings[guild_id]:
        user_warnings = warnings[guild_id][user_id]
        if user_warnings:
          embed = discord.Embed(title=f"Warnings for {user.name}#{user.discriminator}",color=discord.Color.red())
          for warning in user_warnings:
            embed.add_field(name=f"Case #{warning['case_number']}",value=f"**Reason:** {warning['reason']}\n**Date:** {warning['date']}",inline=False)
          await interaction.response.send_message(embed=embed)
        else:
          await interaction.response.send_message(f"{user.name}#{user.discriminator} has no warnings.")
      else:
        await interaction.response.send_message(f"No warnings found for {user.name}#{user.discriminator} in this guild.")
    except Exception as error:
            await on_general_error(interaction, error)
  else:
    await interaction.response.send_message(premium_message)

@bot.tree.command()
async def warn(interaction: discord.Interaction, user: discord.User, *,reason: str):
  '''Log a warning against a user in the server.'''
  guild_id=interaction.guild.id
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    try:
      current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      guild_id = str(interaction.guild.id)
      user_id = str(user.id)
      staff_roles = get_staff_roles(guild_id)
      management_roles = get_management_roles(guild_id)
      is_staff = any(role.id in staff_roles for role in interaction.user.roles)
      is_management = any(role.id in management_roles for role in interaction.user.roles)
      is_admin = interaction.user.guild_permissions.administrator
      if is_staff == True or is_management == True or is_admin == True:
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
            embed = discord.Embed(title="User Warned",description=f"{user.mention} got warned for {reason}. Case Number: {case_number}",color=0xFF0000)
            await interaction.response.send_message(embed=embed)
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
  else:
    await interaction.response.send_message(premium_message)


@bot.tree.command()
async def membercount(interaction: discord.Interaction):
  '''Gives the total number of members in server.'''
  guild_id = interaction.guild.id
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    embed = discord.Embed(
        description=f"{interaction.guild.member_count} members.", color=0x0F00FF)
    await interaction.response.send_message(embed=embed)
  else:
    await interaction.response.send_message(premium_message)

@bot.command()
async def membercount(interaction: discord.Interaction):
  '''Gives the total number of members in server.'''
  embed = discord.Embed(
      description=f"{interaction.guild.member_count} members.", color=0x00FF00)
  await interaction.channel.send(embed=embed)

@bot.tree.command()
async def promote(interaction: discord.Interaction, member: discord.Member, *,old_rank: discord.Role, next_rank: discord.Role,approved: discord.Role, reason: str):
  '''Promote Server Staff'''
  guild_id = interaction.guild.id
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    try:
      managemet_role = get_management_roles(guild_id)
      if any(role.id in managemet_role for role in interaction.user.roles) or interaction.user.guild_permissions.administrator:
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
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.")
    except Exception as error:
          await on_general_error(interaction, error)
  else:
    await interaction.response.send_message(premium_message)

@bot.tree.command()
async def demote(interaction: discord.Interaction, member: discord.Member, *,old_rank: discord.Role, next_rank: discord.Role,approved: discord.Role, reason: str):
  '''Demote Server Staff'''
  guild_id = interaction.guild.id
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    try:
      managemet_role = get_management_roles(guild_id)
      if any(role.id in managemet_role for role in interaction.user.roles) or interaction.user.guild_permissions.administrator:
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
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.")
    except Exception as error:
          await on_general_error(interaction, error)
  else:
    await interaction.response.send_message(premium_message)

@bot.tree.command()
async def passapp(interaction: discord.Interaction, member: discord.Member, *,
                  server_message: str, feedback: str):
  '''Post Passed Application Result'''
  guild_id = interaction.guild.id
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    try:
      managemet_role = get_management_roles(guild_id)
      if any(role.id in managemet_role for role in interaction.user.roles) or (
          interaction.user.guild_permissions.administrator):
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
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.")
    except Exception as error:
          await on_general_error(interaction, error)
  else:
    await interaction.response.send_message(premium_message)

@bot.tree.command()
async def failapp(interaction: discord.Interaction, member: discord.Member, *,
                  feedback: str):
  '''Post Failed Application result.'''
  guild_id = interaction.guild.id
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    try:
      managemet_role = get_management_roles(guild_id)
      if any(role.id in managemet_role for role in interaction.user.roles) or (
          interaction.user.guild_permissions.administrator):
          channel = interaction.channel
          embed = discord.Embed(
              title=f"{interaction.guild.name} Application Failed.", color=0xFF0000)
          embed.add_field(name="Staff Name", value=member.mention)
          embed.add_field(name="Feedback", value=feedback)
          embed.add_field(name="Signed By", value=interaction.user.mention)
          await interaction.response.send_message("Result Sent", ephemeral=True)
          await channel.send(member.mention, embed=embed)
      else:
          await interaction.response.send_message(
              "❌ You don't have permission to use this command.")
    except Exception as error:
          await on_general_error(interaction, error)
  else:
    await interaction.response.send_message(premium_message)

@bot.tree.command()
async def modloggerchannel(interaction: discord.Interaction,channel: discord.TextChannel):
    '''Add Moderation Log Channel'''
    guild_id=interaction.guild.id
    server_config = get_server_config(guild_id)
    premium_status = server_config.get("premium", [])
    if 'false' in premium_status:
      try:
          if interaction.user.guild_permissions.administrator == True:
              try:
                  with open("server_config.json", "r") as file:
                      server_config = json.load(file)
                  guild_id = str(interaction.guild.id)
                  server_config[guild_id]["mod_log_channel"] = channel.id
                  with open("server_config.json", "w") as file:
                      json.dump(server_config, file, indent=4)
                  embed = discord.Embed(title="Server Config Changed",description=f"Added {channel.mention} as a Moderation Log.",color=0x0000FF)
                  await interaction.response.send_message(embed=embed)
              except Exception as e:
                  await interaction.response.send_message("Internal Error Occurred.")
          else:
              await interaction.response.send_message("❌ You don't have permission to use this command.")
      except Exception as error:
          await on_general_error(interaction, error)
    else:
      await interaction.response.send_message(premium_message)

@bot.tree.command()
async def purge(interaction: discord.Interaction, amount: int):   
    '''Purge messages from channel'''
    server_config = get_server_config(guild_id)
    premium_status = server_config.get("premium", [])
    if 'false' in premium_status:
      try:
          guild_id = interaction.guild.id
          managemet_role = get_management_roles(guild_id)
          staff_role = get_staff_roles(guild_id)
          if (any(role.id in managemet_role for role in interaction.user.roles)
              or any(role.id in staff_role for role in interaction.user.roles)):
              if amount == 50:
                  await interaction.response.send_message(f'Cleared {amount} messages.')
                  await interaction.channel.purge(limit=amount + 1)
              else:
                  await interaction.response.send_message("Discord Rate limiter only supports max 50 purge at a time!")
          else:
              await interaction.response.send_message("❌ You don't have permission to use this command.")
      except Exception as error:
          await on_general_error(interaction, error)
    else:
      await interaction.response.send_message(premium_message)

@bot.command(name='custom')
async def custom_command(ctx, action, command_name=None):
  guild_id = str(ctx.guild.id)
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    staff_roles = get_staff_roles(guild_id)
    management_roles = get_management_roles(guild_id)
    is_staff = any(role.id in staff_roles for role in ctx.author.roles)
    is_management = any(role.id in management_roles for role in ctx.author.roles)
    is_admin = ctx.author.guild_permissions.administrator
    if is_staff == True or is_management == True or is_admin == True:
      if action == 'run':
        await run_custom_command(ctx, command_name)
      elif action == 'create':
        await create_custom_command(ctx, command_name)
      elif action == 'delete':
        await delete_custom_command(ctx, command_name)
      else:
        await ctx.send("Invalid action. Use '!custom run [command_name]', '!custom create [command_name]', or '!custom delete [command_name]'.")
    else:
      await ctx.send("❌ You don't have permission to use this command.")
  else:
    await ctx.send(premium_message)
  
async def run_custom_command(ctx, command_name):
    config = load_customcommand()
    guild_id = str(ctx.guild.id)
    command_details = config.get(guild_id, {}).get(command_name)
    if command_details:
        embed = discord.Embed(
            title=command_details.get('title', ''),
            description=command_details.get('description', ''),
            color=command_details.get('colour', discord.Color.default().value))
        image_url = command_details.get('image_url')
        if image_url:
            embed.set_image(url=image_url)
        channel_id = command_details.get('channel')
        channel = bot.get_channel(channel_id)
        role_id = command_details.get('role')
        if role_id:
            role = ctx.guild.get_role(role_id)
            if role:
                await channel.send(f"<@&{role_id}>")  
            else:
                await ctx.send("Role not found. Please make sure the role exists.")
                return
        await channel.send(embed=embed)
        await ctx.send(f"Custom command '{command_name}' executed in {channel.mention}.")
    else:
        await ctx.send(f"Custom command '{command_name}' not found.")

async def create_custom_command(ctx, command_name):
    config = load_customcommand()
    guild_id = str(ctx.guild.id)
    if command_name in config.get(guild_id, {}):
        await ctx.send(f"Custom command '{command_name}' already exists.")
        return
    if len(config.get(guild_id, {})) >= 5:
        await ctx.send("Sorry, the server has reached the maximum limit of custom commands (5).")
        return
    await ctx.send("Enter embed title:")
    title = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
    await ctx.send("Enter embed description:")
    description = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
    await ctx.send("Enter embed colour (hex format, e.g., #RRGGBB):")
    colour = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
    await ctx.send("Enter image URL (enter 'none' for no image):")
    image_url_input = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
    await ctx.send("Enter default channel to post message (mention the channel):")
    channel_input = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
    await ctx.send("Enter role ID to ping:")
    role_id_input = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
    channel_id = int(channel_input.content[2:-1])
    role_id = int(role_id_input.content)
    try:
        color_decimal = int(colour.content[1:], 16)
    except ValueError:
        await ctx.send("Invalid hex color format. Please use the format #RRGGBB.")
        return
    image_url = image_url_input.content.strip()
    if image_url.lower() == 'none':
        image_url = None
    if len(config.get(guild_id, {})) >= 5:
        await ctx.send("Sorry, the server has reached the maximum limit of custom commands (5).")
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
    await ctx.send(f"Custom command '{command_name}' created successfully.")


async def delete_custom_command(ctx, command_name):
  config = load_customcommand()
  guild_id = str(ctx.guild.id)
  command_details = config.get(guild_id, {}).get(command_name)
  if command_details:
    del config[guild_id][command_name]
    save_customcommand(config)
    await ctx.send(f"Custom command '{command_name}' deleted successfully.")
  else:
    await ctx.send(f"Custom command '{command_name}' not found.")


@bot.command(name='whois')
async def whois(ctx, *, user_info=None):
    guild_id = str(ctx.guild.id)
    server_config = get_server_config(guild_id)
    premium_status = server_config.get("premium", [])
    if 'false' in premium_status:
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
    else:
      await ctx.send(premium_message)

@bot.command(name='pick')
async def pick(ctx, option1, option2):
  guild_id = str(ctx.guild.id)
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    option = random.choice([option1, option2])
    await ctx.send(f"I pick {option}")
  else:
    await ctx.send(premium_message)

@bot.command()
async def catimage(ctx):
  guild_id = str(ctx.guild.id)
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    response = requests.get("https://api.thecatapi.com/v1/images/search")
    data = response.json()
    image_url = data[0]["url"]
    image_response = requests.get(image_url)
    image_data = Image.open(BytesIO(image_response.content))
    with BytesIO() as image_bytes:
      image_data.save(image_bytes, format='PNG')
      image_bytes.seek(0)
      await ctx.send(file=discord.File(image_bytes, 'cat_image.png')) 
  else:
    await ctx.send(premium_message)

@bot.command()
async def dogimage(ctx):
    response = requests.get("https://api.thedogapi.com/v1/images/search")
    data = response.json()
    image_url = data[0]["url"]
    image_response = requests.get(image_url)
    image_data = Image.open(BytesIO(image_response.content))
    with BytesIO() as image_bytes:
      image_data.save(image_bytes, format='PNG')
      image_bytes.seek(0)
      await ctx.send(file=discord.File(image_bytes, 'cat_image.png'))

@bot.tree.command()
async def getavatar(interaction: discord.Interaction, user: discord.User):
  '''Get any user avatar from server'''
  guild_id = interaction.guild.id
  server_config = get_server_config(guild_id)
  premium_status = server_config.get("premium", [])
  if 'false' in premium_status:
    try:
        '''Get User Avatar'''
        embed = discord.Embed(title=f"{user.name}'s Profile Photo", color=0x00FFFF)
        embed.set_image(url=user.avatar)
        await interaction.response.send_message(embed=embed)
    except Exception as error:
        await on_general_error(interaction, error)
  else:
    await interaction.response.send_message(premium_message)

@bot.event
async def on_general_error(ctx, error):
    error_uid = str(uuid.uuid4())
    log_error(error, error_uid)
    if isinstance(ctx, discord.Interaction):
        embed = discord.Embed(title="An error occurred",description=f"An error occurred (Error UID: {error_uid}). Please contact support.",color=0xFF0000)
        await ctx.channel.send(embed=embed)
    else:
        await ctx.channel.send(f"An error occurred (Error UID: {error_uid}). Please contact support.")

def log_error(error, error_uid):
    print(f"An error occurred - Error UID: {error_uid}")
    traceback.print_exception(type(error), error, error.__traceback__)
    try:
        with open('cerror.json', 'r') as file:
            errors = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        errors = []
    errors.append({'uid': error_uid,'message': str(error),'traceback': traceback.format_exc()
    })
    with open('cerror.json', 'w') as file:
        json.dump(errors, file, indent=2)

bot.run("YOUR_TOKEN_HERE")