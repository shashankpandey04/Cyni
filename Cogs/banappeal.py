import discord

from discord.ext import commands
from db import mycon

class Appeal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="appeal", brief="Ban Appeal Commands", description="Ban Appeal Commands", usage="banappeal")
    async def appeal(self, ctx):
        pass

    @appeal.command(name="approve", brief="Approve a ban appeal", description="Approve a ban appeal", usage="banappeal approve")
    @commands.guild_only()
    async def approve(self, ctx,user_id:str):
        cursor = mycon.cursor()
        user_id = int(user_id)
        cursor.execute("SELECT * FROM ban_appeals WHERE user_id = %s AND guild_id = %s AND status = 'pending'", (user_id, ctx.guild.id))
        ban_appeal = cursor.fetchone()
        if ban_appeal:
            cursor.execute("UPDATE ban_appeals SET status = 'approved' WHERE user_id = %s AND guild_id = %s", (user_id, ctx.guild.id))
            mycon.commit()
            cursor.close()
            await ctx.send(f"Ban Appeal for <@{user_id}> has been approved.")
            user = self.bot.get_user(user_id)
            await user.send(f"Your Ban Appeal in {ctx.guild} has been approved.")
            await ctx.guild.unban(user)
        else:
            await ctx.send(f"Ban Appeal for <@{user_id}> not found.")

    @appeal.command(name="deny", brief="Deny a ban appeal", description="Deny a ban appeal", usage="banappeal deny")
    @commands.guild_only()
    async def deny(self, ctx,user_id:str):
        cursor = mycon.cursor()
        user_id = int(user_id)
        cursor.execute("SELECT * FROM ban_appeals WHERE user_id = %s AND guild_id = %s", (user_id, ctx.guild.id))
        ban_appeal = cursor.fetchone()
        if ban_appeal:
            cursor.execute("DELETE FROM ban_appeals WHERE user_id = %s AND guild_id = %s", (user_id, ctx.guild.id))
            mycon.commit()
            cursor.close()
            await ctx.send(f"Ban Appeal for <@{user_id}> has been denied.")
            user = self.bot.get_user(user_id)
            await user.send(f"Your Ban Appeal in {ctx.guild} has been denied.")
        else:
            await ctx.send(f"Ban Appeal for <@{user_id}> not found.")

async def setup(bot):
    await bot.add_cog(Appeal(bot))