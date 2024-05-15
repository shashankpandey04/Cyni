import discord
from discord.ext import commands
from utils import check_permissions, modlogchannel
from db import mycon as db
from cyni import on_command_error
class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="warn")
    async def warn(self, ctx, user: discord.Member, *, reason: str):
        '''Warns a user'''
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
            guild_id = str(ctx.guild.id)
            user_id = str(user.id)
            moderator_id = str(ctx.author.id)
            timestamp = str(ctx.message.created_at)
            reason = str(reason)
            cursor = db.cursor()
            sql = "SELECT MAX(warning_id) FROM warnings WHERE guild_id = %s"
            cursor.execute(sql, (guild_id,))
            result = cursor.fetchone()
            highest_warning_id = result[0] if result[0] is not None else 0
            new_warning_id = highest_warning_id + 1
            sql = "INSERT INTO warnings (guild_id, warning_id, user_id, reason, moderator_id, timestamp) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (guild_id, new_warning_id, user_id, reason, moderator_id, timestamp)
            cursor.execute(sql, val)
            db.commit()
            cursor.close()
            emoji_server_id = 1228305781938720779
            emoji_server = self.bot.get_guild(emoji_server_id)
            caution = discord.utils.get(emoji_server.emojis, id=1240175679245647933)
            arrow = discord.utils.get(emoji_server.emojis, id=1240175302077059135)
            await ctx.send(f"{caution} Case No. {new_warning_id}. {user} has been warned for {reason}.")
            embed = discord.Embed(title="User Warned", color=0x2F3136)
            embed.add_field(name=f"{arrow} Warning ID", value=new_warning_id, inline=False)
            embed.add_field(name=f"{arrow} User", value=user.mention, inline=False)
            embed.add_field(name=f"{arrow} Moderator", value=ctx.author.mention, inline=False)
            embed.add_field(name=f"{arrow} Reason", value=reason, inline=False)
            await mod_log_channel.send(embed=embed)
            #send it to user too.
            embed = discord.Embed(title=f"You got warned in {ctx.guild} for {reason}", color=0x2F3136)
            embed.add_field(name=f"{arrow} Warning ID", value=new_warning_id, inline=False)
            embed.add_field(name=f"{arrow} Moderator", value=ctx.author.mention, inline=False)
            embed.add_field(name=f"{arrow} Reason", value=reason, inline=False)
            await user.send(embed=embed)
        except Exception as error:
            await on_command_error(ctx, error)

async def setup(bot):
    await bot.add_cog(Warn(bot))
