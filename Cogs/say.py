import discord
from discord.ext import commands
import requests
from cyni import on_command_error
from utils import check_permissions

class Say(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.hybrid_command(name="say",aliases=["s"])
    async def say(self,ctx, message: str):
        '''Broadcasts a message in the channel'''
        channel = ctx.channel
        if await check_permissions(ctx, ctx.author):
            try:
                await ctx.send(message)
            except Exception as e:
                await on_command_error(ctx,e)
        else:
            await ctx.send("❌ You are not permitted to use this command",ephemeral=True)

async def setup(bot):
   await bot.add_cog(Say(bot))