import discord
from discord.ext import commands
import datetime
from utils import *

@commands.command(name='warn')
async def prefix_warn(ctx, user: discord.User, *, reason: str):
    '''Log warning against user in server.'''
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    guild_id = str(ctx.guild.id)
    user_id = str(user.id)
    staff_roles = get_staff_roles(guild_id)

    if any(role.id in staff_roles for role in ctx.author.roles):
        mod_log_channel_id = modlogchannel(guild_id)
        if mod_log_channel_id is not None:
            mod_log_channel = ctx.guild.get_channel(mod_log_channel_id)
            if mod_log_channel:
                if guild_id not in warnings:
                    warnings[guild_id] = {}
                if user_id not in warnings[guild_id]:
                    warnings[guild_id][user_id] = []

                case_number = get_next_case_number(guild_id, user_id)
                warnings[guild_id][user_id].append({
                    'case_number': case_number,
                    'reason': reason,
                    'date': current_datetime
                })

                save_data()

                embed = discord.Embed(title="User Warned", description=f"{user.mention} got warned for {reason}. Case Number: {case_number}", color=0xFF0000)
                await ctx.send(embed=embed)

                log_embed = discord.Embed(title="Moderation Log", color=0xFF0000)
                log_embed.add_field(name="Case Number", value=str(case_number))
                log_embed.add_field(name="User", value=user.mention)
                log_embed.add_field(name="Action", value="Warn")
                log_embed.add_field(name="Reason", value=reason)
                log_embed.add_field(name="Moderator", value=ctx.author.mention)
                log_embed.add_field(name="Date", value=current_datetime)

                await mod_log_channel.send(embed=log_embed)
            else:
                await ctx.channel.send("❌ Moderation log channel is not defined in the server configuration.")
        else:
            await ctx.channel.send('❌ Moderation log channel is not defined in the server configuration.')
    else:
        await ctx.channel.send('❌ You do not have permission to use this command.')

        