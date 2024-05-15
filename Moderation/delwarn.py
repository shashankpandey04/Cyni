import discord
from discord.ext import commands
from db import mycon as db
from utils import check_permissions, modlogchannel
from cyni import on_command_error
class DelWarn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="delwarn", aliases=["removewarn","voidwarn","vw"])
    async def delwarn(self, ctx, warning_id: int):
        '''Deletes a warning by its ID'''
        try:
            if not await check_permissions(ctx, ctx.author):
                await ctx.send("❌ You don't have permission to use this command.")
                return
            cursor = db.cursor()
            sql = "DELETE FROM warnings WHERE guild_id = %s AND warning_id = %s"
            val = (str(ctx.guild.id), warning_id)
            cursor.execute(sql, val)
            mod_log_channel_id = modlogchannel(ctx.guild.id)
            mod_log_channel_id = int(mod_log_channel_id) if mod_log_channel_id else None
            db.commit()
            cursor.close()
            if cursor.rowcount == 0:
                await ctx.send(f"⚠️ Warning ID {warning_id} not found.")
            else:
                await ctx.send(f"✅ Warning ID {warning_id} has been deleted.")
                if mod_log_channel_id:
                    mod_log_channel = self.bot.get_channel(mod_log_channel_id)
                    if mod_log_channel:
                        embed = discord.Embed(title="Warning Deleted", color=0x2F3136)
                        embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                        embed.add_field(name="Warning ID", value=warning_id, inline=False)
                        await mod_log_channel.send(embed=embed)
        except Exception as error:
            await on_command_error(ctx, error)

async def setup(bot):
    await bot.add_cog(DelWarn(bot))
