import discord
from discord.ext import commands
import keep_alive
import json
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

logging_channel_id = 1154038613974192168
# Create an instance of the bot
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


# Save warnings to the file
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
      # Send a log message in the logging channel
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
  # Check if the user has one of the high-rank roles
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    await member.send(f'You have been banned from the server for: {reason}')
    await member.ban(reason=reason)
    await ctx.send(f'{member.mention} has been banned for: {reason}')
    logging_channel = bot.get_channel(logging_channel_id)

    if logging_channel:
      # Send a log message in the logging channel
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
  # Check if the user has one of the high-rank roles
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    # Add warning to the dictionary
    if member.id not in warnings:
      warnings[member.id] = []
    warnings[member.id].append(reason)
    save_warnings(warnings)

    # Send a warning message as an embed in the current channel
    embed = discord.Embed(title='User Warning',
                          description=f'Warned {member.mention} for: {reason}',
                          color=discord.Color.red())
    await ctx.send(embed=embed)

    # Send a direct message to the warned user
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
      # Send a log message in the logging channel
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
  # Check if the user has the necessary role to use the command
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    # Convert duration from minutes to seconds
    duration_seconds = duration_minutes * 60

    # Store original channel permissions
    original_overwrites = member.guild_permissions

    # Update member's channel permissions
    overwrite = discord.PermissionOverwrite(send_messages=False)
    for channel in ctx.guild.channels:
      await channel.set_permissions(member, overwrite=overwrite)

    # Send confirmation message
    await ctx.send(
        f"{member.mention} has been muted for {duration_minutes} minutes.")
    logging_channel = bot.get_channel(logging_channel_id)

    if logging_channel:
      # Send a log message in the logging channel
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

    # Restore original channel permissions after the specified duration
  await asyncio.sleep(duration_seconds)
  for channel in ctx.guild.channels:
      await channel.set_permissions(member, overwrite=original_overwrites)
  else:
    await ctx.send("You don't have permission to use this command.")


@bot.command()
async def purge(ctx, amount: int):
  # Check if the user has one of the high-rank roles
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
  # Check if the user has one of the allowed roles
  if any(role.id in high_rank_role_ids for role in ctx.author.roles):
    # Lock the channel by setting permissions
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
  # Check if the user has one of the allowed roles
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

  await ctx.message.delete()  # Delete the user's command message


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


try:
    with open("tickets.txt", "r") as file:
        file_contents = file.read()
        if file_contents:
            user_tickets = json.loads(file_contents)
        else:
            user_tickets = {}
except FileNotFoundError:
    user_tickets = {}



@bot.event
async def on_message(message):
  if message.channel.id == 1153675839519608943:  # Replace with your channel's ID
    if message.author != bot.user:  # Avoid the bot responding to itself
      category = discord.utils.get(message.guild.categories, name="Tickets")
      if category is None:
        category = await message.guild.create_category("Tickets")

      ticket_channel = await category.create_text_channel(
          f"ticket-{message.author.name}")
      await ticket_channel.set_permissions(message.author,
                                           read_messages=True,
                                           send_messages=True)
      await ticket_channel.set_permissions(message.guild.default_role,
                                           read_messages=False)

      user_tickets[str(message.author.id)] = str(
          ticket_channel.id)  # Store channel ID as string

      await ticket_channel.send(
          f"""{message.author.mention}, Here is your ticket with the issue {message.content}.
          **Please wait for response by our Support Team. Don't ping anyone.**
          You can use !close to close the ticket.
          Thanks.
          Qupr Systems"""
      )

      await message.delete()  # Delete the user's message

      # Save updated ticket data back to the file
      with open("tickets.txt", "w") as file:
        json.dump(user_tickets, file, indent=4)

  await bot.process_commands(message)


@bot.command()
async def close(ctx):
  ticket_channel_id = user_tickets.get(str(
      ctx.author.id))  # Convert ID to string
  if ticket_channel_id:
    ticket_channel = bot.get_channel(
        int(ticket_channel_id))  # Convert ID back to int
    if ticket_channel:
      await ticket_channel.delete()
      user_tickets.pop(str(ctx.author.id))
      await ctx.send(f"Your ticket has been closed, {ctx.author.mention}.")

      # Update the text file with the latest ticket data
      with open("tickets.txt", "w") as file:
        json.dump(user_tickets, file, indent=4)
    else:
      await ctx.send(
          "Sorry, there was an issue finding and deleting the ticket.")
  else:
    await ctx.send(f"You don't have an open ticket, {ctx.author.mention}.")


keep_alive.keep_alive()
bot.run("BOT_TOKEN")
