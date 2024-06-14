import discord
from discord.ext import commands
import requests
import logging
from utils import *
import time
from tokens import *
from menu import *
import os
from discord.utils import get
from Modals.roblox_username import LinkRoblox
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
from db import mycon

def dbstatus():
    if mycon.is_connected():
        return "Connected"
    else:
        return "Disconnected"


def get_prefix(bot, message):
    cursor = mycon.cursor()
    query = "SELECT prefix FROM server_config WHERE guild_id = %s"
    cursor.execute(query, (message.guild.id,))
    prefix = cursor.fetchone()
    cursor.close()
    if prefix:
        return prefix[0]
    else:
        return "?"
    
intents = discord.Intents.all()
bot = commands.Bot(command_prefix = get_prefix, intents=intents)
bot.remove_command('help')

cyni_support_role_id = 800203880515633163

BOT_USER_ID = 1136945734399295538
dev = ['1201129677457215558','707064490826530888']
racial_slurs = []
def load_racial_slurs():
    try:
        cursor = mycon.cursor()
        query = "SELECT word FROM block_word"
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            racial_slurs.append(row[0])
    except Exception as e:
        print(f"An error occurred while loading racial slurs: {e}")

load_racial_slurs()

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return
    if message.content.startswith("?jsk shutdown"):
        if message.author.id in dev:
            await message.channel.send("<@800203880515633163> Get to work!")
            return
    if any(slur in message.content.lower() for slur in racial_slurs):
        if message.author.guild_permissions.administrator:
            #print("Admin Bypass")
            return
        await message.delete()
        await message.channel.send(f"{message.author.mention}, your message contained inappropriate content and was removed.")
        #print(f"{message} removed")
        return
    try:
        guild_id = message.guild.id
        user_id = message.author.id
        cursor = mycon.cursor()
        cursor.execute("SELECT * FROM server_config WHERE guild_id = %s", (guild_id,))
        server_config = cursor.fetchone()
        cursor.close()
        if server_config:
            guild_id, staff_roles, management_roles, mod_log_channel, premium, report_channel, blocked_search, anti_ping, anti_ping_roles, bypass_anti_ping_roles, loa_role, staff_management_channel,infraction_channel,promotion_channel,prefix,application_channel,message_quota = server_config
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
                                embed = discord.Embed(title="Anti-Ping Warning", description=f"{message.author.mention} attempted to ping {mentioned_user.mention} in {message.channel.mention}.", color=0xFF0000)
                                embed.set_image(url="https://media.tenor.com/aslruXgPKHEAAAAM/discord-ping.gif")
                                await message.channel.send(embed=embed)
        staff_or_management_roles = get_staff_or_management_roles(guild_id)
        user_roles = [role.id for role in message.author.roles]
        if any(role_id in user_roles for role_id in staff_or_management_roles):
            cursor = mycon.cursor()
            cursor.execute("INSERT INTO activity_logs (user_id, guild_id, messages_sent) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE messages_sent = messages_sent + 1",(user_id, guild_id))
            mycon.commit()
            cursor.close()
    except Exception as e:
        print(f"An error occurred while processing message: {e}")

async def load():
    for directory in ["Cogs", "Roblox", "ImagesCommand", "Staff_Commands", "Moderation"]:
        for filename in os.listdir(f"./{directory}"):
            if filename.endswith('.py'):
                try:
                    await bot.load_extension(f"{directory}.{filename[:-3]}")
                except Exception as e:
                    print(f"Failed to load extension '{filename}': {e}")

@bot.event
async def on_ready():
    await load()
    await bot.tree.sync()
    bot.start_time = time.time()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/help | Cyni"))
    await bot.load_extension("jishaku")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    error_uid = generate_error_uid()
    sentry = discord.Embed(
        title="❌ An error occurred.",
        description=f"Error ID: `{error_uid}`\nThis can be solved by joining our support server.\n[Join Cyni Support](https://discord.gg/2D29TSfNW6)",
        color=0xFF0000
    )
    try:
        if ctx.interaction is not None:
            await ctx.interaction.response.send_message(embed=sentry)
        else:
            await ctx.send(embed=sentry)
        log_error(error, error_uid)
    except:
        log_error(error, error_uid)

@bot.hybrid_group()
async def activity(ctx):
    pass

@activity.command()
async def leaderboard(ctx):
    '''Get activity leaderboard for the server, sorted by messages sent (high to low) with quota check.'''
    try:
        quota = get_message_quota(ctx.guild.id)  # Get guild's message quota
        quota = int(quota) if quota else 100  # Default quota is 100
        mycur = mycon.cursor()
        mycur.execute("SELECT user_id, SUM(messages_sent) AS total_messages FROM activity_logs WHERE guild_id = %s GROUP BY user_id", (ctx.guild.id,))
        activity_data = mycur.fetchall()
        # Sort leaderboard data by total messages (descending order)
        sorted_data = sorted(activity_data, key=lambda x: x[1], reverse=True)
        leaderboard_embed = discord.Embed(title="Activity Leaderboard", color=0x2F3136)
        emoji_server_id = 1228305781938720779
        emoji_server = bot.get_guild(emoji_server_id)
        tick = discord.utils.get(emoji_server.emojis, id=1240174811024461844)
        cross = discord.utils.get(emoji_server.emojis, id=1240175023050719314)
        for user_id, total_messages in sorted_data:
            member = ctx.guild.get_member(user_id)
            if member:
                quota_status = f"{tick}" if total_messages >= quota else f"{cross}"
                leaderboard_embed.add_field(name=f"{member.display_name}", value=f"Total Messages: {total_messages} {quota_status}", inline=False)
        await ctx.send(embed=leaderboard_embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@activity.command()
async def stats(ctx, member: discord.Member):
    '''Get activity stats for a user.'''
    try:
        mycur = mycon.cursor()
        mycur.execute("SELECT * FROM activity_logs WHERE user_id = %s AND guild_id = %s", (member.id, ctx.guild.id))
        activity_data = mycur.fetchall()
        total = len(activity_data)
        if activity_data:
            stats_embed = discord.Embed(title="Activity Stats", color=0x2F3136)
            stats_embed.add_field(name="User ID", value=f"<@{member.id}>",inline=False)
            stats_embed.add_field(name="Total Messages Sent", value=total, inline=False)
            stats_embed.set_thumbnail(url=member.avatar.url)
            await ctx.send(embed=stats_embed)
        else:
            await ctx.send("No activity data found for this user.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
    finally:
        mycur.close()

@activity.command()
async def reset(ctx):
    '''Reset activity stats for the server.'''
    try:
        mycur = mycon.cursor()
        management_roles = get_management_roles(ctx.guild.id)
        if isinstance(management_roles, int):
            management_roles = [management_roles]
        if check_permissions_management(ctx, management_roles):
            embed = discord.Embed(title="Confirm Activity Stats Reset", description="Are you sure you want to reset activity stats?", color=0x2F3136)
            view = ConfirmView()
            await ctx.send(embed=embed, view=view)
            await view.wait()
            if view.value:
                mycur.execute("DELETE FROM activity_logs WHERE guild_id = %s", (ctx.guild.id,))
                mycon.commit()
                await ctx.send("Activity stats reset successfully.")
            else:
                await ctx.send("Activity stats reset canceled.")
        else:
            await ctx.send("You don't have permission to use this command.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
    finally:
        mycur.close()

@bot.event
async def on_guild_join(guild):
    support_server_id = 1152949579407442050
    support_channel_id = 1210248878599839774
    support_server = bot.get_guild(support_server_id)
    support_channel = support_server.get_channel(support_channel_id)
    embed = discord.Embed(title="New Server Joined", color=0x2F3136)
    try:
        embed.set_thumbnail(url=guild.icon.url)
    except:
        pass
    embed.add_field(name="Server Name", value=guild.name, inline=False)
    embed.add_field(name="Server ID", value=guild.id, inline=False)
    embed.add_field(name="Owner", value=guild.owner, inline=False)
    embed.add_field(name="Total Guilds", value=len(bot.guilds), inline=False)
    try:
        embed.add_field(name="Total Members", value=guild.member_count, inline=False)
    except:
        embed.add_field(name="Total Members", value="Unknown", inline=False)
    try:
        embed.add_field(name="Server Region", value=guild.region, inline=False)
    except:
        embed.add_field(name="Server Region", value="Unknown", inline=False)
    try:
        invite_link = await guild.invites()
        embed.add_field(name="Server Invite", value=invite_link[0], inline=False)
    except:
        embed.add_field(name="Server Invite", value="Unknown", inline=False)
    await support_channel.send(embed=embed)
    create_or_get_server_config(guild.id)

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
                try:
                    await member.add_roles(role)
                    embed = discord.Embed(
                        title='Role added.',
                        description=f"Role {role.mention} added to {member.mention}",
                        color=0x2F3136)
                    await ctx.send(embed=embed)
                except Exception as e:
                    await ctx.send(f"An error occurred: {e}")
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
                try:
                    await member.remove_roles(role)
                    embed = discord.Embed(title='Role Removed.', 
                                        description=f"Role {role.mention} is now removed from {member.mention}",
                                        color=0x2F3136)
                    await ctx.send(embed=embed)
                except Exception as e:
                    await ctx.send(f"An error occurred: {e}")
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
async def passed(ctx, member: discord.Member,*,feedback: str):
  '''Post Passed Application Result'''
  try:
      if await check_permissions_management(ctx, ctx.author):
        channel = get_application_channel(ctx.guild.id)
        if channel is not None:
            await ctx.send("❌ Application channel not found.")
            return
        channel = int(channel)
        app_channel = discord.utils.get(ctx.guild.channels, id=channel)
        if channel is None:
          await ctx.send("❌ Application channel not found.")
          return
        else:
            embed = discord.Embed(
            title=f"{ctx.guild.name} | Application Result.", color=0x2F3136)
            embed.add_field(name="Staff Name", value=member.mention)
            embed.add_field(name="Feedback", value=feedback)
            embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="Signed By", value=ctx.author.mention)
            await ctx.send("Result Posted")
            await app_channel.send(member.mention, embed=embed)
      else:
        await ctx.send("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_command_error(ctx, error)

@application.command()
async def failed(ctx, member: discord.Member, *,feedback: str):
  '''Post Failed Application result.'''
  try:
      if await check_permissions_management(ctx, ctx.author):
            channel = get_application_channel(ctx.guild.id)
            if channel is not None:
                await ctx.send("❌ Application channel not found.")
                return
            channel = int(channel)
            app_channel = discord.utils.get(ctx.guild.channels, id=channel)
            if channel is None:
              await ctx.send("❌ Application channel not found.")
            embed = discord.Embed(
                title=f"{ctx.guild.name} | Application Result.", 
                color=0x2F3136)
            embed.add_field(name="Staff Name", value=member.mention)
            embed.add_field(name="Feedback", value=feedback)
            embed.add_field(name="Signed By", value=ctx.author.mention)
            embed.set_thumbnail(url=member.avatar.url)
            await ctx.send("Result Posted")
            await app_channel.send(member.mention, embed=embed)
      else:
          await ctx.send("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_command_error(ctx, error)

@bot.hybrid_group()
async def staff(ctx):
    pass

@staff.command()
async def infract(ctx, member: discord.Member, *, rank: discord.Role, reason: str):
    '''Infract Server Staff'''
    try:
        if await check_permissions_management(ctx, ctx.author):
            channel_id = get_infraction_channel(ctx.guild.id)  # Get the channel ID
            if channel_id is None:
                await ctx.send("❌ Infraction channel not found.")
                return

            infraction_channel = get(ctx.guild.channels, id=int(channel_id))  # Get the channel object
            if infraction_channel is None:
                await ctx.send("❌ Infraction channel not found.")
                return

            embed = discord.Embed(
                title=f"{ctx.guild.name} | Staff Infractions.", color=0x2F3136)
            embed.add_field(name="Staff Name", value=member.mention)
            embed.add_field(name="Feedback", value=reason)
            embed.add_field(name="Rank", value=rank.mention)
            embed.add_field(name="Signed By", value=ctx.author.mention)
            embed.set_thumbnail(url=member.avatar.url)

            await ctx.send("Infraction Sent")
            await infraction_channel.send(member.mention, embed=embed)
        else:
            await ctx.send("❌ You don't have permission to use this command.")
    except Exception as error:
        await on_command_error(ctx, error)


@staff.command()
async def promote(ctx, member: discord.Member, *, rank: discord.Role, approval: discord.Role, reason: str):
    '''Promote Server Staff'''
    try:
        if await check_permissions_management(ctx, ctx.author):
            channel_id = get_promo_channel(ctx.guild.id)  # Get the channel ID
            #converting channel_id into integer
            if channel_id is None:
                await ctx.send("❌ Promo channel not found.")
                return
            channel_id = int(channel_id)
            print(channel_id)
            promo_channel = discord.utils.get(ctx.guild.channels, id=channel_id)  # Get the channel object
            print(promo_channel)
            if promo_channel is None:
                await ctx.send("❌ Promo channel not found.")
                return
            
            embed = discord.Embed(title=f"{ctx.guild.name} Promotions.", color=0x2F3136)
            embed.add_field(name="Staff Name", value=member.mention)
            embed.add_field(name="New Rank", value=rank.mention)
            embed.add_field(name="Approved By", value=approval.mention)
            embed.add_field(name="Reason", value=reason)
            embed.add_field(name="Signed By", value=ctx.author.mention)
            embed.set_thumbnail(url=member.avatar.url)
            
            try:
                await member.remove_roles(approval)
                await member.add_roles(rank)
                await ctx.send("Promotion Sent")
                await promo_channel.send(member.mention, embed=embed)  # Send response to promo channel
            except Exception as e:
                await ctx.send("Promotion Sent")
                await promo_channel.send(member.mention, embed=embed)
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
async def run(ctx,command_name:str):
    '''Run Custom Command'''
    if await check_permissions(ctx, ctx.author):
          await run_custom_command(ctx, command_name)
          embed = discord.Embed(title="Custom Command Executed",description=f"Custom Command {command_name} executed by {ctx.author.mention}",color=0x00FF00)
          await ctx.send(embed=embed)
    else:
      await ctx.send("❌ You don't have permission to use this command.")

@custom.command()
async def list(ctx):
    '''List Custom Commands'''
    await list_custom_commands(ctx)

@custom.command()
async def manage(ctx, action:str, name:str):
    '''Manage Custom Commands (create, delete, list)'''
    guild_id = ctx.guild.id
    try:
        if await check_permissions_management(ctx, ctx.author):
            if action == 'create':
                await create_custom_command(ctx, name) 
            elif action == 'delete':
                await delete_custom_command(ctx, name)
            else:
                await ctx.send("Invalid action. Valid actions are: create, delete")
                await ctx.channel.purge(limit=1)
        else:
            await ctx.send("❌ You don't have permission to use this command.")
    except Exception as error:
          await on_command_error(ctx, error)

async def load_custom_command(ctx):
    try:
        guild_id = str(ctx.guild.id)
        if mycon.is_connected():
            cursor = mycon.cursor(dictionary=True)
            cursor.execute("SELECT * FROM custom_commands where guild_id = %s", (guild_id,))
            rows = cursor.fetchall()
            config = {}
            for row in rows:
                guild_id = str(row['guild_id'])
                command_name = row['command_name']
                title = row['title']
                description = row['description']
                color = row['color']
                image_url = row['image_url']
                channel = row['channel']
                role = row['role']
                if guild_id not in config:
                    config[guild_id] = {}
                config[guild_id][command_name] = {
                    'title': title,
                    'description': description,
                    'colour': color,
                    'image_url': image_url,
                    'channel': channel,
                    'role': role
                }
            return config
    except Exception as e:
        print("Error while connecting to MySQL", e)
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
    return {}

async def list_custom_commands(ctx):
    config = await load_custom_command(ctx)
    guild_id = str(ctx.guild.id)
    custom_commands = config.get(guild_id, {})
    if not custom_commands:
        await ctx.send(embed=discord.Embed(description="No custom commands found for this server.",color=0x2F3136))
        return
    embed = discord.Embed(title="Custom Commands", color=0x2F3136)
    for name, details in custom_commands.items():
        channel = ctx.guild.get_channel(details.get('channel'))
        role_mention = f"<@&{details.get('role')}>" if details.get('role') else "N/A"
        embed.add_field(
            name=f"Command Name: {name}",
            value=f"**Channel:** {channel.mention if channel else 'N/A'}\n**Role Mention:** {role_mention}",
            inline=False
        )
    await ctx.send(embed=embed)

async def run_custom_command(ctx, command_name):
    try:
        mycur = mycon.cursor()
        guild_id = str(ctx.guild.id)
        mycur.execute("SELECT * FROM custom_commands WHERE guild_id = %s AND command_name = %s", (guild_id, command_name))
        command_details = mycur.fetchone()
        if command_details:
            title = command_details[2]
            description = command_details[3]
            color = discord.Colour(int(command_details[4]))  # Convert to discord.Colour
            embed = discord.Embed(
                title=title,
                description=description,
                color=color
            )
            embed.set_footer(text="Executed By: " + ctx.author.name)
            if command_details[5]:
                embed.set_image(url=command_details[5])
            channel_id = command_details[6]
            channel = bot.get_channel(channel_id)
            role_id = command_details[7]
            if role_id:
                role = ctx.guild.get_role(role_id)
                if role:
                    await channel.send(f"<@&{role_id}>")  
                else:
                    await ctx.send("Role not found. Please make sure the role exists.")
                    return
            await channel.send(embed=embed)
        else:
            await ctx.send(f"Custom command '{command_name}' not found.")
    except Exception as e:
        print(f"An error occurred while running custom command: {e}")
    finally:
        mycur.close()

async def create_custom_command(ctx, command_name):
    try:
        mycur = mycon.cursor()
        guild_id = str(ctx.guild.id)
        mycur.execute("SELECT * FROM custom_commands WHERE guild_id = %s AND command_name = %s", (guild_id, command_name))
        existing_command = mycur.fetchone()
        if existing_command:
            await ctx.channel.send(f"Custom command '{command_name}' already exists.")
            return
        mycur.execute("SELECT COUNT(*) FROM custom_commands WHERE guild_id = %s", (guild_id,))
        command_count = mycur.fetchone()[0]
        if command_count >= 5:
            await ctx.channel.send("Sorry, the server has reached the maximum limit of custom commands (5).")
            return
        await ctx.channel.send("Enter embed title:")
        title = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
        await ctx.channel.send("Enter embed description:")
        description = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
        await ctx.channel.send("Enter embed colour (hex format, e.g., #RRGGBB):")
        colour = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
        await ctx.channel.send("Enter image URL (enter 'none' for no image):")
        image_url_input = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
        await ctx.channel.send("Enter default channel to post message (mention the channel):")
        channel_input = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
        await ctx.channel.send("Enter role ID to ping (enter 'none' for no role):")
        role_id_input = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
        channel_id = int(channel_input.content[2:-1])
        role_id = int(role_id_input.content) if role_id_input.content.lower() != 'none' else None
        try:
            color_decimal = int(colour.content[1:], 16)
        except ValueError:
            await ctx.send("Invalid hex color format. Please use the format #RRGGBB.")
            return
        image_url = image_url_input.content.strip()
        image_url = None if image_url.lower() == 'none' else image_url
        channel_id_str = channel_input.content.strip('<#>')
        try:
            channel_id = int(channel_id_str)
        except ValueError:
            await ctx.send("Invalid channel mention. Please mention a valid channel.")
            return
        mycur.execute("INSERT INTO custom_commands (guild_id, command_name, title, description, color, image_url, channel, role) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (guild_id, command_name, title.content, description.content, color_decimal, image_url, channel_id, role_id))
        mycon.commit()
        await ctx.send(f"Custom command '{command_name}' created successfully.")
    except Exception as e:
        print(f"An error occurred while creating custom command: {e}")
    finally:
        mycur.close()
    
async def delete_custom_command(interaction, command_name):
    try:
        mycur = mycon.cursor()
        guild_id = str(interaction.guild.id)
        mycur.execute("SELECT * FROM custom_commands WHERE guild_id = %s AND command_name = %s", (guild_id, command_name))
        existing_command = mycur.fetchone()

        if not existing_command:
            await interaction.channel.send(f"Custom command '{command_name}' not found.")
            return
        mycur.execute("DELETE FROM custom_commands WHERE guild_id = %s AND command_name = %s", (guild_id, command_name))
        mycon.commit()
        await interaction.channel.send(f"Custom command '{command_name}' deleted successfully.")
    except Exception as e:
        print(f"An error occurred while deleting custom command: {e}")
    finally:
        mycur.close()

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
        if interaction.user.roles == cyni_support_role_id:
            cursor = mycon.cursor()
            cursor.execute("SELECT * FROM error_logs WHERE uid = %s", (error_uid,))
            error_log = cursor.fetchone()
            if error_log:
                uid, message, traceback, created_at = error_log[1:]
                embed = discord.Embed(title="Error Log",description=f"Error UID: `{uid}`",color=0x2F3136)
                embed.add_field(name="Message", value=message, inline=False)
                embed.add_field(name="Traceback", value=traceback, inline=False)
                embed.add_field(name="Created At", value=created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"No error log found for UID `{error_uid}`.")
        else:
            await interaction.response.send_message("❌ You don't have permission to use this command.")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred while fetching the error log: {e}")
    finally:
        cursor.close()

@bot.tree.command()
async def linkroblox(interaction:discord.Interaction):
    '''Link Roblox Account'''
    user_id = interaction.user.id
    cursor = mycon.cursor()
    cursor.execute("SELECT * FROM roblox_user WHERE user_id = %s", (user_id,))
    roblox_user = cursor.fetchone()
    if roblox_user:
        await interaction.response.send_message("❌ You have already linked a Roblox account.")
    else:
        await interaction.response.send_modal(LinkRoblox())
        
@bot.tree.command()
async def prefix(interaction:discord.Interaction,prefix:str):
    '''Change Prefix'''
    if await check_permissions(interaction, interaction.user):
        guild_id = interaction.guild.id
        cursor = mycon.cursor()
        cursor.execute("UPDATE server_config SET prefix = %s WHERE guild_id = %s", (prefix, guild_id))
        mycon.commit()
        cursor.close()
        await interaction.response.send_message(f"Prefix changed to `{prefix}`.")
    else:
        await interaction.response.send_message("❌ You don't have permission to use this command.")

TOKEN = os.getenv('PRODUCTION_TOKEN')
if TOKEN:
    logging.info("Using Production Token.")
else:
    TOKEN = os.getenv("DEVELOPMENT_TOKEN")
    if TOKEN:
        logging.info("Using Development Token.")
    else:
        logging.error("No token found.")
        exit()

def cyni():
    bot.run(TOKEN)

if __name__ == '__main__':
    cyni()