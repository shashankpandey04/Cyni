import discord
from discord.ext import commands
from db import mycon as db
class WarnLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="warnlog")
    async def warnlog(self, ctx, user: discord.Member = None):
        '''Shows the warning log of a user'''
        user = user or ctx.author
        cursor = db.cursor()
        sql = "SELECT warning_id, reason, moderator_id, timestamp FROM warnings WHERE guild_id = %s AND user_id = %s ORDER BY warning_id"
        cursor.execute(sql, (str(ctx.guild.id), str(user.id)))
        warnings = cursor.fetchall()
        cursor.close()
        if not warnings:
            await ctx.send(f"{user.mention} has no warnings.")
            return
        embed = discord.Embed(title=f"Warning Log for {user}", color=discord.Color.orange())
        for warning in warnings:
            warning_id, reason, moderator_id, timestamp = warning
            embed.add_field(
                name=f"Warning ID {warning_id}",
                value=f"**Reason**: {reason}\n**Moderator**: <@{moderator_id}>\n**Timestamp**: {timestamp}",
                inline=False
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WarnLog(bot))
