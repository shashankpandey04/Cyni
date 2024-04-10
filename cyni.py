import discord
from discord.ext import commands
import requests
import logging
from utils import *
import time
import random
from tokens import get_token
from menu import *
import psutil
import json
import os
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
from db import *
import re
import aiohttp

def dbstatus():
    if mycon.is_connected():
        return "Connected"
    else:
        return "Disconnected"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=':', intents=intents)
bot.remove_command('help')

async def load(bot):
    for filename in os.listdir('./Cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'Cogs.{filename[:-3]}')
            print(f'Loaded {filename}')
    for filename in os.listdir("./Roblox"):
        if filename.endswith(".py"):
            await bot.load_extension(f"Roblox.{filename[:-3]}")
            print(f"Loaded {filename}")
    for filename in os.listdir("./ImagesCommand"):
        if filename.endswith(".py"):
            await bot.load_extension(f"ImagesCommand.{filename[:-3]}")
            print(f"Loaded {filename}")
    for filename in os.listdir("./Staff_Commands"):
        if filename.endswith(".py"):
            await bot.load_extension(f"Staff_Commands.{filename[:-3]}")
            print(f"Loaded {filename}")

@bot.event
async def on_ready():
    try:
        await load(bot)
    except Exception as e:
        print(f"Error occurred during cog loading: {e}")
    await bot.tree.sync()
    bot.start_time = time.time()
    for guild in bot.guilds:
        create_or_get_server_config(guild.id)
    cleanup_guild_data(bot)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/support | Cyni"))
    await bot.load_extension("jishaku")
    print(f'Logged in as {bot.user.name} - {bot.user.id}')

cyni_support_role_id = 800203880515633163
@bot.event
async def on_thread_create(ctx):
    print("Thread created!")
    if ctx.channel.parent_id == 1158047746159284254:
        await ctx.send(f"<@{cyni_support_role_id}")
        await ctx.purge(limit=1)
    else:
        return
bot_owner_id = '1201129677457215558'
BOT_USER_ID = 1136945734399295538

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return
    elif message.content.startswith("?jsk shutdown"):
        await message.channel.send("<@1201129677457215558> Get to work!\n<@707064490826530888> You also!")
        return
    await check_for_racial_slurs(message)
    if bot.user.mentioned_in(message) and str(message.author.id) == bot_owner_id:
        await message.channel.send("Deployment triggered! 🚀")
        deployment_url = "http://172.93.103.105:3000/api/deploy/d410185117e4bfa2a60c17f26234b44091ee1b47cdae5aca"
        async with aiohttp.ClientSession() as session:
            async with session.get(deployment_url) as response:
                if response.status == 200:
                    print("Deployment successful")
                else:
                    print("Deployment failed")
        return
    try:
        guild_id = message.guild.id
        user_id = message.author.id
        cursor.execute("SELECT * FROM server_config WHERE guild_id = %s", (guild_id,))
        server_config = cursor.fetchone()
        if server_config:
            guild_id, staff_roles, management_roles, mod_log_channel, premium, report_channel, blocked_search, anti_ping, anti_ping_roles, bypass_anti_ping_roles, loa_role, staff_management_channel = server_config
            if anti_ping == 1:
                anti_ping_roles = anti_ping_roles or [] 
                bypass_anti_ping_roles = bypass_anti_ping_roles or [] 
                if message.mentions:
                    mentioned_user = message.mentions[0]
                    author_has_bypass_role = any(str(role.id) in bypass_anti_ping_roles for role in message.author.roles)
                    has_management_role = any(str(role.id) in anti_ping_roles for role in mentioned_user.roles)
                    if not author_has_bypass_role:
                        if has_management_role:
                            author_can_warn = any(str(role.id) in anti_ping_roles for role in message.author.roles)
                            if not author_can_warn:
                                warning_message = f"{message.author.mention} Refrain from pinging users with Anti-ping enabled role, if it's not necessary."
                                await message.channel.send(warning_message)
        staff_or_management_roles = get_staff_or_management_roles(guild_id)
        user_roles = [role.id for role in message.author.roles]
        if any(role_id in user_roles for role_id in staff_or_management_roles):
            mycur.execute("INSERT INTO activity_logs (user_id, guild_id, messages_sent) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE messages_sent = messages_sent + 1", (user_id, guild_id))
            mycon.commit()
    except Exception as e:
        print(f"An error occurred while processing message: {e}")

@bot.hybrid_group()
async def activity(ctx):
    pass

@activity.command()
async def leaderboard(ctx):
    try:
        mycur.execute("SELECT user_id, SUM(messages_sent) AS total_messages FROM activity_logs WHERE guild_id = %s GROUP BY user_id", (ctx.guild.id,))
        activity_data = mycur.fetchall()
        leaderboard_embed = discord.Embed(title="Activity Leaderboard", color=0x2F3136)
        for user_id, total_messages in activity_data:
            member = ctx.guild.get_member(user_id)
            if member:
                leaderboard_embed.add_field(name=member.display_name, value=f"Total Messages: {total_messages}", inline=False)
        await ctx.send(embed=leaderboard_embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@activity.command()
async def clear(ctx):
    if await check_permissions_management(ctx,ctx.author):
        try:
            embed = discord.Embed(title="Manage Activity")
            embed.add_field(name="What it does?",value="From this command you can reset your server's Activity leaderboard.")
            mycur.execute(f"DELTE FROM activity_logs where guild_id = '{ctx.guild.id}'")
            await ctx.send("✅Leaderboard Reset | Successfully.")
        except Exception as error:
            await on_command_error(ctx,error)
    else:
        await no_permission()
            
@bot.event
async def on_command_error(ctx, error):
    existing_uids = get_existing_uids()
    error_uid = generate_error_uid(existing_uids)
    sentry = discord.Embed(
        title="❌ An error occurred.",
        description=f"Error I'd `{error_uid}`\nThis can be solved by joining our support server.\n[Join Cyni Support](https://discord.gg/2D29TSfNW6)",
        color=0xFF0000
    )
    sentry.add_field(name="Error", value=error, inline=False)
    await ctx.send(embed=sentry)
    log_error(error, error_uid)

existing_uids = get_existing_uids()

@bot.event
async def on_guild_join(guild):
    support_server_id = 1152949579407442050
    support_channel_id = 1210248878599839774
    support_server = bot.get_guild(support_server_id)
    support_channel = support_server.get_channel(support_channel_id)
    embed = discord.Embed(title="New Server Joined", color=0x00ff00)
    embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Server Name", value=guild.name, inline=False)
    embed.add_field(name="Server ID", value=guild.id, inline=False)
    embed.add_field(name="Owner", value=guild.owner, inline=False)
    embed.add_field(name="Total Guilds", value=len(bot.guilds), inline=False)
    await support_channel.send(embed=embed)
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
        await on_command_error(interaction,e)
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
          await on_command_error(interaction, error)

"""@bot.hybrid_group()
async def modmail(ctx):
    pass

@modmail.command()
async def blacklist(ctx,member:discord.Member):
    '''Blacklist user from opening mod mails.'''
    await ctx.send(f"{member.mention} have been blacklisted!")

@modmail.command()
async def close(ctx):
    '''Close Mod Mail Channel.'''
    await ctx.send("Mod Mail closed.")

@modmail.command()
async def open(ctx,reason:str):
    '''Open Mod Mail Channel.'''
    await ctx.send(f"Mod Mail opened for the reason {reason}")

@modmail.command()
async def adduser(ctx,member:discord.Member):
    '''Add user to Mod Mail Channel.'''
    await ctx.send(f"{member.mention} added to Mod Mail Channel.")

@modmail.command()
async def removeuser(ctx,member:discord.Member):
    '''Remove user from Mod Mail Channel.'''
    await ctx.send(f"{member.mention} removed from Mod Mail Channel.")
"""
@bot.hybrid_group()
async def role(ctx):
    pass

@role.command()
async def add(ctx, member: discord.Member, role: discord.Role):
    '''Add a role to member'''
    try:
        if await check_permissions(ctx, ctx.author):
            if not ctx.author.guild_permissions.manage_roles:
                await ctx.response.send_message("❌ You don't have the 'Manage Roles' permission.")
            else:
                await member.add_roles(role)
                embed = discord.Embed(
                    title='Role added.',
                    description=f"Role {role.mention} added to {member.mention}",
                    color=0x00FF00)
                await ctx.send(embed=embed)
        else:
            await ctx.send("❌ You don't have permission to use this command.")
    except Exception as error:
        await on_command_error(ctx, error)

@role.command()
async def remove(ctx, member: discord.Member, role: discord.Role):
    '''Add a role to member'''
    try:
        if await check_permissions(ctx, ctx.author):
            if not ctx.author.guild_permissions.manage_roles:
                await ctx.send("❌ You don't have the 'Manage Roles' permission.")
            else:
                await member.remove_roles(role)
                embed = discord.Embed(title='Role Removed.', description=f"Role {role.mention} is now removed from {member.mention}", color=0xFF0000)
                await ctx.send(embed=embed)
        else:
            await ctx.send("❌ You don't have permission to use this command.")
    except Exception as error:
        await on_command_error(ctx, error)

@bot.tree.command()
async def membercount(interaction: discord.Interaction):
  '''Gives the total number of members in server.'''
  await interaction.response.send_message(f"{interaction.guild.member_count} members.")

@bot.hybrid_group()
async def application(ctx):
    pass

@application.command()
async def passed(interaction: discord.Interaction, member: discord.Member, *,server_message: str, feedback: str):
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
          await on_command_error(interaction, error)

@application.command()
async def failed(interaction: discord.Interaction, member: discord.Member, *,feedback: str):
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
          await on_command_error(interaction, error)

@bot.hybrid_group()
async def staff(ctx):
    pass

@staff.command()
async def infract(ctx, member: discord.Member, *,server_message: str, feedback: str):
  '''Post Infractions Result'''
  try:
      if await check_permissions_management(ctx, ctx.author):
        channel = ctx.channel
        embed = discord.Embed(
        title=f"{ctx.guild.name} Staff Infractions.", color=0x2F3136)
        embed.add_field(name="Staff Name", value=member.mention)
        embed.add_field(name="Server Message", value=server_message)
        embed.add_field(name="Feedback", value=feedback)
        embed.add_field(name="Signed By", value=ctx.author.mention)
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send("Result Sent")
        await channel.send(member.mention, embed=embed)
      else:
        await ctx.send("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_command_error(ctx, error)

@staff.command()
async def promote(ctx, member: discord.Member, *,old_rank: discord.Role, next_rank: discord.Role,approved: discord.Role, reason: str):
  '''Promote Server Staff'''
  try:
      if await check_permissions_management(ctx, ctx.author):
        channel = ctx.channel
        embed = discord.Embed(title=f"{ctx.guild.name} Promotions.",color=0x2F3136)
        embed.add_field(name="Staff Name", value=member.mention)
        embed.add_field(name="Old Rank", value=old_rank.mention)
        embed.add_field(name="New Rank", value=next_rank.mention)
        embed.add_field(name="Approved By", value=approved.mention)
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Signed By", value=ctx.author.mention)
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send("Promotion Sent")
        await channel.send(member.mention, embed=embed)
      else:
        await ctx.send("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_command_error(ctx, error)

@staff.command()
async def demote(ctx, member: discord.Member, *,old_rank: discord.Role, next_rank: discord.Role,approved: discord.Role, reason: str,channel: discord.TextChannel):
  '''Demote Server Staff'''
  try:
      if await check_permissions_management(ctx, ctx.author):
        channel = ctx.channel
        embed = discord.Embed(title=f"{ctx.guild.name} Demotions.",color=0x2F3136)
        embed.add_field(name="Staff Name", value=member.mention)
        embed.add_field(name="Old Rank", value=old_rank.mention)
        embed.add_field(name="New Rank", value=next_rank.mention)
        embed.add_field(name="Approved By", value=approved.mention)
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Signed By", value=ctx.author.mention)
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send("Demotion Sent", ephemeral=True)
        await channel.send(member.mention, embed=embed)
      else:
        await ctx.send("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_command_error(ctx, error)

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
          await on_command_error(interaction, error)

@bot.hybrid_group()
async def custom(ctx):
    pass

@custom.command()
async def run(interaction:discord.Interaction,command_name:str):
    '''Run Custom Command'''
    if await check_permissions(interaction, interaction.user):
          await run_custom_command(interaction, command_name)
          embed = discord.Embed(title="Custom Command Executed",description=f"Custom Command {command_name} executed by {interaction.user.mention}",color=0x00FF00)
          await interaction.response.send_message(embed=embed)
    else:
      await interaction.response.send_message("❌ You don't have permission to use this command.")

@custom.command()
async def manage(interaction:discord.Interaction, action:str, name:str):
    '''Manage Custom Commands (create, delete, list)'''
    guild_id = interaction.guild.id
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
          await on_command_error(interaction, error)

def load_custom_command(interaction):
    try:
        guild_id = str(interaction.guild.id)
        if db.is_connected():
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM custom_commands where guild_id = %s", (guild_id,))
            rows = cursor.fetchall()
            print("Rows:", rows)
            config = {}
            for row in rows:
                guild_id = str(row['guild_id'])
                command_name = row['command_name']
                title = row['title']
                description = row['description']
                color = row['color']
                image_url = row['image_url']
                if guild_id not in config:
                    config[guild_id] = {}
                config[guild_id][command_name] = {
                    'title': title,
                    'description': description,
                    'colour': color,
                    'image_url': image_url
                }
            print("Config:", config)
            return config
    except Exception as e:
        print("Error while connecting to MySQL", e)
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
    return {}

async def list_custom_commands(interaction):
    embeds = list_custom_commands_embeds(interaction)
    for embed in embeds:
        await interaction.channel.send(embed=embed)

async def run_custom_command(interaction, command_name):
    guild_id = str(interaction.guild.id)
    mycur.execute("SELECT * FROM custom_commands WHERE guild_id = %s AND command_name = %s", (guild_id, command_name))
    command_details = mycur.fetchone()

    if command_details:
        embed = discord.Embed(
            title=command_details[2],
            description=command_details[3],
            color=command_details[4]
        )
        embed.set_footer(text="Executed By: " + interaction.user.name)
        if command_details[5]:
            embed.set_image(url=command_details[5])
        
        channel_id = command_details[6]
        channel = bot.get_channel(channel_id)
        role_id = command_details[7]

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
    guild_id = str(interaction.guild.id)
    mycur.execute("SELECT * FROM custom_commands WHERE guild_id = %s AND command_name = %s", (guild_id, command_name))
    existing_command = mycur.fetchone()
    if existing_command:
        await interaction.response.send_message(f"Custom command '{command_name}' already exists.")
        return
    mycur.execute("SELECT COUNT(*) FROM custom_commands WHERE guild_id = %s", (guild_id,))
    command_count = mycur.fetchone()[0]
    if command_count >= 5:
        await interaction.response.send_message("Sorry, the server has reached the maximum limit of custom commands (5).")
        return
    await interaction.response.send_message("Enter embed title:")
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
    role_id = int(role_id_input.content) if role_id_input.content.lower() != 'none' else None
    try:
        color_decimal = int(colour.content[1:], 16)
    except ValueError:
        await interaction.channel.send("Invalid hex color format. Please use the format #RRGGBB.")
        return
    image_url = image_url_input.content.strip()
    image_url = None if image_url.lower() == 'none' else image_url
    channel_id_str = channel_input.content.strip('<#>')
    try:
        channel_id = int(channel_id_str)
    except ValueError:
        await interaction.channel.send("Invalid channel mention. Please mention a valid channel.")
        return
    mycur.execute("INSERT INTO custom_commands (guild_id, command_name, title, description, color, image_url, channel, role) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (guild_id, command_name, title.content, description.content, color_decimal, image_url, channel_id, role_id))
    mycon.commit()
    await interaction.channel.send(f"Custom command '{command_name}' created successfully.")
    
async def delete_custom_command(interaction, command_name):
    guild_id = str(interaction.guild.id)
    mycur.execute("SELECT * FROM custom_commands WHERE guild_id = %s AND command_name = %s", (guild_id, command_name))
    existing_command = mycur.fetchone()

    if not existing_command:
        await interaction.channel.send(f"Custom command '{command_name}' not found.")
        return

    mycur.execute("DELETE FROM custom_commands WHERE guild_id = %s AND command_name = %s", (guild_id, command_name))
    mycon.commit()

    await interaction.channel.send(f"Custom command '{command_name}' deleted successfully.")

@bot.tree.command()
async def pick(interaction: discord.Interaction, option1:str, option2:str):
  '''Pick between two options'''
  option = random.choice([option1, option2])
  await interaction.response.send_message(f"I pick {option}")

@bot.command(name='pick')
async def pick(ctx, option1, option2):
  option = random.choice([option1, option2])
  await ctx.send(f"I pick {option}")

@bot.hybrid_group()
async def image(ctx):
    pass

@image.command()
async def cat(interaction:discord.Interaction):
  '''Get Random Cat Image'''
  response = requests.get("https://api.thecatapi.com/v1/images/search")
  data = response.json()
  image_url = data[0]["url"]
  embed = discord.Embed(title="Random Cat Image", color=0x2F3136)
  embed.set_image(url=image_url)
  await interaction.response.send_message(embed=embed)

@image.command()
async def dog(interaction: discord.Interaction):
    '''Get Random Dog Image'''
    response = requests.get("https://api.thedogapi.com/v1/images/search")
    data = response.json()
    image_url = data[0]["url"]
    embed = discord.Embed(title="Random Dog Image", color=0x2F3136)
    embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed)

@image.command()
async def bird(interaction: discord.Interaction):
    '''Get Random Bird Image'''
    response = requests.get("https://birbapi.astrobirb.dev/birb")
    data = response.json()
    image_url = data["image_url"]
    embed = discord.Embed(title="Random Bird Image", color=0x2F3136)
    embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command()
async def avatar(interaction: discord.Interaction, user: discord.User):
  '''Get any user avatar from server'''
  try:
    embed = discord.Embed(title=f"{user.name}'s Profile Photo", color=0x2F3136)
    embed.set_image(url=user.avatar)
    await interaction.response.send_message(embed=embed)
  except Exception as error:
        await on_command_error(interaction, error)

@bot.hybrid_group()
async def roblox(ctx):
    pass

@roblox.command()
async def userid(ctx,userid:int):
    '''Get Roblox User Info by User ID'''
    api_url = f"https://users.roblox.com/v1/users/{userid}"
    avatar_api_url = f"https://www.roblox.com/avatar-thumbnails?params=[{{userId:{userid}}}]"
    response = requests.get(avatar_api_url)
    avatar_data = response.json()[0]
    thumbnail_url = avatar_data["thumbnailUrl"]
    response = requests.get(api_url)
    try:
        if response.status_code == 200:
            data = response.json()
            embed = discord.Embed(title="User Info", color=0x2F3136)
            embed.add_field(name="Rolox ID", value=data["id"], inline=False)
            embed.add_field(name="Username", value=data["name"], inline=True)
            embed.add_field(name="Display Name",value=data["displayName"],inline=False)
            embed.add_field(name="Description",value=data["description"],inline=True)
            embed.set_thumbnail(url=thumbnail_url)
            embed.add_field(name="Is Banned", value=data["isBanned"], inline=False)
            embed.add_field(name="Has Verified Badge",value=data["hasVerifiedBadge"],inline=True)
            embed.add_field(name="Created", value=data["created"], inline=False)
            await ctx.send(embed=embed)
    except Exception as error:
        await on_command_error(ctx,error)

@roblox.command()
async def username(ctx,username:str):
    '''Get Roblox User Info by Username'''
    api_url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": True}
    response = requests.post(api_url, json=payload)
    if response.status_code == 200:
        data = response.json()["data"][0]
        try:
            userid = data["id"]
            await ctx.send(embed=robloxusername(userid))
        except Exception as e:
            await on_command_error(ctx,e)
    else:
        await ctx.send("User not found.")

cyni_support_role_id = 1158043149424398406
@bot.tree.command()
async def sentry(interaction:discord.Interaction, error_uid:str):
    try:
        cursor.execute("SELECT * FROM error_logs WHERE uid = %s", (error_uid,))
        error_log = cursor.fetchone()
        if error_log:
            uid, message, traceback, created_at = error_log
            embed = discord.Embed(title="Error Log",description=f"Error UID: `{uid}`",color=0x2F3136)
            embed.add_field(name="Message", value=message, inline=False)
            embed.add_field(name="Traceback", value=traceback, inline=False)
            embed.add_field(name="Created At", value=created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"No error log found for UID `{error_uid}`.")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred while fetching the error log: {e}")

@bot.tree.command()
async def whois(interaction:discord.Interaction, user_info:str):
    guild_id = str(interaction.guild.id)
    server_config = get_server_config(guild_id)
    if user_info is None:
          member = interaction.user
    else:
          if user_info.startswith('<@') and user_info.endswith('>'):
              user_id = int(user_info[2:-1])
              member = interaction.guild.get_member(user_id)
          else:
              member = discord.utils.find(lambda m: m.name == user_info, interaction.guild.members)
    if member:
          support_server_id = 1152949579407442050
          support_server = bot.get_guild(support_server_id)
          user_emoji = discord.utils.get(support_server.emojis, id=1191057214727786598)
          cyni_emoji = discord.utils.get(support_server.emojis, id=1185563043015446558)
          discord_emoji = discord.utils.get(support_server.emojis, id=1191057244004044890)
          with open('staff.json', 'r') as file:
              staff_data = json.load(file)
          embed = discord.Embed(title="User Information", color=0x2F3136)
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
          if member == member.guild.owner:
              embed.add_field(name="Role", value="Server Owner", inline=True)
          elif member.guild_permissions.administrator:
              embed.add_field(name="Role", value="Administrator", inline=True)
          elif member.guild_permissions.manage_messages:
              embed.add_field(name="Role", value="Moderator", inline=True)
          else:
              embed.add_field(name="Role", value="Member", inline=True)
          embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
          await interaction.response.send_message(embed=embed)
    else:
          await interaction.response.send_message("User not found.")

@bot.tree.command()
async def support(interaction:discord.Interaction):
  '''Join Cyni Support Server'''
  embed = discord.Embed(title="Cyni Support Server",description="Need any help?\nJoin Cyni Support Server.",color=0x2F3136)
  await interaction.response.send_message(embed=embed ,view=SupportBtn())

@bot.tree.command()
async def servermanage(interaction:discord.Interaction):
  '''Manage Your Server with Cyni'''
  try:
    if interaction.user.guild_permissions.administrator:
      embed = discord.Embed(title="Server Manage",description='''
                          **Staff Roles:**
                          - *Discord Staff Roles:* These roles grant permission to use Cyni's moderation commands.\n
                          - *Management Roles:* Users with these roles can utilize Cyni's management commands, including Application Result commands, Staff Promo/Demo command, and setting the Moderation Log channel.

                          **Server Config:**
                          - Easily view and edit your server configuration settings.

                          **Anti-ping Module:**
                          - Messages are sent if a user with specific roles attempts to ping anyone. Bypass roles can be configured to allow certain users to ping others with that role.

                          **Support Server:**
                          - Need assistance? Join the Cyni Support Server for help.
                            '''
                            ,color=0x2F3136) 
      await interaction.response.send_message(embed=embed, view=SetupView(),ephemeral=True)
    else:
      await interaction.response.send_message("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_command_error(interaction, error)

'''@bot.hybrid_group()
async def web(ctx):
    pass

@web.command()
async def block(interaction:discord.Interaction, keyword: str):
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

@web.command()
async def search(interaction:discord.Interaction, topic: str):
  """Search on web using CYNI Search API"""
  guild_id = str(interaction.guild.id)
  server_config = get_server_config(guild_id)
  blocked_search = server_config.get('blocked_search', [])
  if topic in blocked_search:
      await interaction.response.send_message("Blocked word found in search query.")
      return
  result = search_api(topic)
  await interaction.response.send_message(f"{result}....")'''

@bot.tree.command()
async def ping(interaction: discord.Interaction):
    '''Check the bot's ping, external API response times, and system RAM usage.'''
    latency = round(bot.latency * 1000)
    db = dbstatus()
    support_server_id = 1152949579407442050
    support_server = bot.get_guild(support_server_id)
    database_emoji = discord.utils.get(support_server.emojis, id=1215565017718587422)
    angle_right = discord.utils.get(support_server.emojis,id=1215565088589877299)()
    ram_usage = psutil.virtual_memory().percent
    uptime_seconds = time.time() - bot.start_time
    uptime_string = time.strftime('%Hh %Mm %Ss', time.gmtime(uptime_seconds))
    embed = discord.Embed(title='Bot Ping', color=0x2F3136)
    embed.add_field(name=f'{angle_right} 🟢 Pong!', value=f"{latency}ms", inline=True)
    embed.add_field(name=f'{angle_right} Uptime', value=uptime_string, inline=True)
    embed.add_field(name=f'{angle_right} System RAM Usage', value=f"{ram_usage}%", inline=True)
    embed.add_field(name=f"{database_emoji} Database Status", value=db, inline=True)
    embed.add_field(name=f"{angle_right} Bot Version", value="6.2.0", inline=True)
    embed.set_thumbnail(url=bot.user.avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command()
async def joke(interaction:discord.Interaction):
   joke = fetch_random_joke()
   await interaction.response.send_message(joke)

@bot.tree.command()
async def vote(interaction:discord.Interaction):
    embed = discord.Embed(title="Vote Cyni!")
    await interaction.response.send_message(embed=embed,view=VoteView())

TOKEN = get_token()
def cyni():
   bot.run(TOKEN)
