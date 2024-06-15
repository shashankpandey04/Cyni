import discord
from discord.ext import commands

import logging
from utils import *
import time
from tokens import *
from menu import *

import logging
from Modals.ban_appeal import BanAppealModal
import os
from discord.utils import get

from dotenv import load_dotenv
import os

load_dotenv()

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
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Patch 6.5"))
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

@bot.hybrid_command()
async def membercount(ctx):
    '''Gives the total number of members in server.'''
    await ctx.send(f"{ctx.guild.member_count} members.")
    
@bot.hybrid_group()
async def application(ctx):
    pass

@application.command()
async def passed(ctx, member: discord.Member,*,feedback: str):
  '''Post Passed Application Result'''
  try:
      if await check_permissions_management(ctx, ctx.author):
        channel = get_application_channel(ctx.guild.id)
        if channel is None:
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
            if channel is None:
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
            #print(channel_id)
            promo_channel = discord.utils.get(ctx.guild.channels, id=channel_id)  # Get the channel object
            #print(promo_channel)
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

@bot.hybrid_command()
async def purge(ctx, amount: int):   
  '''Purge messages from channel'''
  try:
    if await check_permissions(ctx, ctx.author):
      await ctx.send(f'Cleared {amount} messages.',ephemeral=True)
      await ctx.channel.purge(limit=amount + 1)      
    else:
      await ctx.send("❌ You don't have permission to use this command.")
  except Exception as error:
          await on_command_error(ctx, error)

@bot.hybrid_command()
async def sentry(ctx, error_uid: str):
    '''Get Error Log by Error UID'''
    try:
        if check_support_role(bot, ctx.author):
            cursor = mycon.cursor()
            cursor.execute("SELECT * FROM error_logs WHERE uid = %s", (error_uid,))
            error_log = cursor.fetchone()
            if error_log:
                uid, message, traceback, created_at = error_log[1:]
                embed = discord.Embed(title="Error Log", description=f"Error UID: `{uid}`", color=0x2F3136)
                embed.add_field(name="Message", value=message, inline=False)
                embed.add_field(name="Traceback", value=traceback, inline=False)
                embed.add_field(name="Created At", value=discord_timestamp(created_at), inline=False)
                await ctx.send(embed=embed)
                cursor.close()
            else:
                await ctx.send("Error log not found.")
        else:
            await ctx.send("❌ You don't have permission to use this command.")
    except Exception as e:
        await on_command_error(ctx, e)
        
@bot.hybrid_command()
async def prefix(ctx,prefix:str):
    '''Change Prefix'''
    if await check_permissions_management(ctx, ctx.author):
        guild_id = ctx.guild.id
        cursor = mycon.cursor()
        cursor.execute("UPDATE server_config SET prefix = %s WHERE guild_id = %s", (prefix, guild_id))
        mycon.commit()
        cursor.close()
        await ctx.send(f"Prefix changed to `{prefix}`.")
    else:
        await ctx.send("❌ You don't have permission to use this command.")

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

@bot.tree.command()
async def banappeal(interaction: discord.Interaction):
    '''Appeal a Ban'''
    await interaction.response.send_modal(BanAppealModal(bot))

def cyni():
    bot.run(TOKEN)

if __name__ == '__main__':
    cyni()