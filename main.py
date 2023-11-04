import discord
from discord.ext import commands
import keep_alive
import json
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

logging_channel_id = 1154038613974192168
bot = commands.Bot(command_prefix='!', intents=intents)

activity_info = "QUPR Systems!"


@bot.event
async def on_ready():
  await bot.change_presence(activity=discord.Activity(
      type=discord.ActivityType.watching, name="QuprSystems!"))


user_tickets = {}

high_rank_role_ids = [1153667071285149789, 1152951022885535804]


def load_warnings():
  warnings = {}
  try:
    with open('warnings.txt', 'r') as file:
      lines = file.readlines()
      for line in lines:
        user_id, *warnings_list = line.strip().split(',')
        warnings[int(user_id)] = warnings_list
  except FileNotFoundError:
    pass
  return warnings

def save_warnings(warnings):
  with open('warnings.txt', 'w') as file:
    for user_id, warnings_list in warnings.items():
      file.write(f'{user_id},{",".join(warnings_list)}\n')


warnings = load_warnings()


@bot.event
async def on_ready():
  print(f'Bot is online and ready as {bot.user}')


@bot.command()
async def kick(ctx,
               member: discord.Member,
               *,
               reason: str = "No reason provided"):
  # Check if the user has one of the high-rank roles
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    await member.send(f'You have been kicked from the server for: {reason}')
    await member.kick(reason=reason)
    await ctx.send(f'{member.mention} has been kicked for: {reason}')
    logging_channel = bot.get_channel(logging_channel_id)

    if logging_channel:
      log_embed = discord.Embed(
          title='User Kicked',
          description=
          f'User {member.display_name} Kicked by {ctx.author.display_name} for: {reason}',
          color=discord.Color.red())
      await logging_channel.send(embed=log_embed)
      print(
          f'User {member.display_name} kicked by {ctx.author.display_name} for: {reason}'
      )
    else:
      print("Logging channel not found.")
  else:
    await ctx.send('You don\'t have permission to use this command.')
  await ctx.message.delete()



@bot.command()
async def ban(ctx,
              member: discord.Member,
              *,
              reason: str = "No reason provided"):
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    await member.send(f'You have been banned from the server for: {reason}')
    await member.ban(reason=reason)
    await ctx.send(f'{member.mention} has been banned for: {reason}')
    logging_channel = bot.get_channel(logging_channel_id)

    if logging_channel:
      log_embed = discord.Embed(
          title='User Banned',
          description=
          f'User {member.display_name} banned by {ctx.author.display_name} for: {reason}',
          color=discord.Color.red())
      await logging_channel.send(embed=log_embed)
      print(
          f'User {member.display_name} banned by {ctx.author.display_name} for: {reason}'
      )
    else:
      print("Logging channel not found.")
  else:
    await ctx.send('You don\'t have permission to use this command.')
  await ctx.message.delete()


@bot.command()
async def warn(ctx, member: discord.Member, *, reason: str):
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    # Add warning to the dictionary
    if member.id not in warnings:
      warnings[member.id] = []
    warnings[member.id].append(reason)
    save_warnings(warnings)

    embed = discord.Embed(title='User Warning',
                          description=f'Warned {member.mention} for: {reason}',
                          color=discord.Color.red())
    await ctx.send(embed=embed)
    try:
      dm_embed = discord.Embed(
          title='You Have Been Warned',
          description=f'You have been warned for: {reason}',
          color=discord.Color.red())
      await member.send(embed=dm_embed)
    except discord.Forbidden:
      await ctx.send(f"Couldn't send a direct message to {member.mention}.")

    logging_channel = bot.get_channel(logging_channel_id)

    if logging_channel:
      log_embed = discord.Embed(
          title='User Warning',
          description=
          f'User {member.display_name} warned by {ctx.author.display_name} for: {reason}',
          color=discord.Color.red())
      await logging_channel.send(embed=log_embed)
      print(
          f'User {member.display_name} warned by {ctx.author.display_name} for: {reason}'
      )
    else:
      print("Logging channel not found.")
  else:
    await ctx.send('You don\'t have permission to use this command.')
  await ctx.message.delete()


@bot.command()
async def timeout(ctx, member: discord.Member, duration_minutes: int):
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    duration_seconds = duration_minutes * 60

    original_overwrites = member.guild_permissions

    overwrite = discord.PermissionOverwrite(send_messages=False)
    for channel in ctx.guild.channels:
      await channel.set_permissions(member, overwrite=overwrite)

    await ctx.send(
        f"{member.mention} has been muted for {duration_minutes} minutes.")
    logging_channel = bot.get_channel(logging_channel_id)

    if logging_channel:
      log_embed = discord.Embed(
          title='User Muted',
          description=
          f'User {member.display_name} muted by {ctx.author.display_name}',
          color=discord.Color.red())
      await logging_channel.send(embed=log_embed)
      print(
          f'User {member.display_name} muted by {ctx.author.display_name} for: {reason}'
      )
    else:
      print("Logging channel not found.")
  else:
    await ctx.send('You don\'t have permission to use this command.')
  await ctx.message.delete()
  await asyncio.sleep(duration_seconds)
  for channel in ctx.guild.channels:
      await channel.set_permissions(member, overwrite=original_overwrites)
  else:
    await ctx.send("You don't have permission to use this command.")


@bot.command()
async def purge(ctx, amount: int):
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    if 1 <= amount <= 100:
      await ctx.message.delete()
      deleted = await ctx.channel.purge(limit=amount + 1)
      await ctx.send(f'Deleted {len(deleted) - 1} messages.')
    else:
      await ctx.send(
          'Please provide a number between 1 and 100 for the amount of messages to delete.'
      )
  else:
    await ctx.send('You don\'t have permission to use this command.')
  await ctx.message.delete()


@bot.command()
async def lock(ctx):
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    overwrite = discord.PermissionOverwrite()
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role,
                                      overwrite=overwrite)

    embed = discord.Embed(
        title="Channel Locked",
        description=
        "This channel has been locked. Only authorized users can send messages.",
        color=discord.Color.red())
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(
        title="Permission Denied",
        description="You don't have permission to use this command.",
        color=discord.Color.red())
    await ctx.send(embed=embed)
  await ctx.message.delete()


@bot.command()
async def unlock(ctx):
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    # Unlock the channel by removing permission overwrites
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=None)

    embed = discord.Embed(
        title="Channel Unlocked",
        description=
        "This channel has been unlocked. All users can send messages now.",
        color=discord.Color.green())
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(
        title="Permission Denied",
        description="You don't have permission to use this command.",
        color=discord.Color.red())
    await ctx.send(embed=embed)

  await ctx.message.delete()


@bot.command()
async def warnlog(ctx, member: discord.Member):
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    if member.id in warnings:
      warning_list = '\n'.join([
          f'{index + 1}. {warning}'
          for index, warning in enumerate(warnings[member.id])
      ])

      embed = discord.Embed(title=f"Warning Log for {member.display_name}",
                            description=warning_list,
                            color=discord.Color.orange())
      await ctx.send(embed=embed)
    else:
      embed = discord.Embed(title="No Warnings Found",
                            description="No warnings found for this user.",
                            color=discord.Color.green())
      await ctx.send(embed=embed)
  else:
    embed = discord.Embed(
        title="Permission Denied",
        description="You don't have permission to use this command.",
        color=discord.Color.red())
    await ctx.send(embed=embed)

  await ctx.message.delete() 


@bot.command()
async def delwarn(ctx, member: discord.Member, warning_id: int):
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    if member.id in warnings and 1 <= warning_id <= len(warnings[member.id]):
      removed_warning = warnings[member.id].pop(warning_id - 1)
      save_warnings(warnings)

      embed = discord.Embed(
          title=f"Removed Warning for {member.display_name}",
          description=
          f"Warning ID: {warning_id}\nRemoved Warning: {removed_warning}",
          color=discord.Color.green())
      await ctx.send(embed=embed)
    else:
      embed = discord.Embed(
          title="Invalid Warning ID or No Warnings Found",
          description=
          "Please provide a valid warning ID or ensure the user has warnings.",
          color=discord.Color.red())
      await ctx.send(embed=embed)
  else:
    embed = discord.Embed(
        title="Permission Denied",
        description="You don't have permission to use this command.",
        color=discord.Color.red())
    await ctx.send(embed=embed)

  await ctx.message.delete()


@bot.command()
async def promo(ctx, user: discord.Member, previous_rank, new_rank,
                approved_rank):
  user_high_rank_roles = [
      role for role in ctx.author.roles if role.id in high_rank_role_ids
  ]
  if user_high_rank_roles:
    qupr_emoji_id = 1140547606230093874  # Replace with your emoji ID
    qupr_emoji = await ctx.guild.fetch_emoji(qupr_emoji_id)
    response = (f"{qupr_emoji}**QUPR System Promotion Update**{qupr_emoji}\n\n"
                f"Staff: {user.mention}\n"
                f"Previous Rank: {previous_rank}\n"
                f"New Rank: {new_rank}\n"
                f"Approved By: {approved_rank}\n\n"
                f"Signed by: {ctx.author.mention}")
    await ctx.send(response)
    await ctx.message.delete()

  else:
    await ctx.send("You do not have the required role to use this command.")
  await ctx.message.delete()

keep_alive.keep_alive()
bot.run("BOT_TOKEN")
