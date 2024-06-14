import discord
from discord.ext import commands
from utils import check_permissions, modlogchannel
from db import mycon as db
from cyni import on_command_error

import logging
class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="kick")
    async def kick(self, ctx, user: discord.Member, *, reason: str):
        '''Kicks a user'''
        try:
            if not await check_permissions(ctx, ctx.author):
                await ctx.send("❌ You don't have permission to use this command.")
                return
            mod_log_channel_id = modlogchannel(ctx.guild.id)
            if not mod_log_channel_id:
                await ctx.send("Please set a modlog channel first.")
                return
            mod_log_channel = self.bot.get_channel(int(mod_log_channel_id))
            if not mod_log_channel:
                await ctx.send("Modlog channel not found. Please check the configuration.")
                return
            timestamp = str(ctx.message.created_at)
            reason = str(reason)
            emoji_server_id = 1228305781938720779
            emoji_server = self.bot.get_guild(emoji_server_id)
            caution = discord.utils.get(emoji_server.emojis, id=1240175679245647933)
            arrow = discord.utils.get(emoji_server.emojis, id=1240175302077059135)
            await ctx.send(f"{caution} User {user} have been kicked for {reason}.")
            await user.kick(reason=reason)
            embed = discord.Embed(title="User Kicked", color=0x2F3136)
            embed.add_field(name=f"{arrow} User", value=user.mention, inline=False)
            embed.add_field(name=f"{arrow} Moderator", value=ctx.author.mention, inline=False)
            embed.add_field(name=f"{arrow} Reason", value=reason, inline=False)
            embed.add_field(name=f"{arrow} Timestamp", value=timestamp, inline=False)
            await mod_log_channel.send(embed=embed)
            #send it to user too.
            embed = discord.Embed(title=f"You got kicked from {ctx.guild} for {reason}", color=0x2F3136)
            embed.add_field(name=f"{arrow} Moderator", value=ctx.author.mention, inline=False)
            embed.add_field(name=f"{arrow} Reason", value=reason, inline=False)
            embed.add_field(name=f"{arrow} Guild Invite Link", value=f"{ctx.guild.text_channels[0].create_invite()}", inline=False)
            try:
                await user.send(embed=embed)
            except:
                logging.error(f"Couldn't send a DM to {user} for warning.")
        except Exception as error:
            await on_command_error(ctx, error)

async def setup(bot):
    await bot.add_cog(Kick(bot))
