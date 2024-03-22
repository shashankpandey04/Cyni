import discord
from discord.ext import commands
from menu import VoteView

class Vote(commands.Cog):
    def __init__ (self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} loaded Vote Cog.")
    
    @commands.command()
    async def vote(self,ctx):
        embed = discord.Embed(title="Vote Cyni!")
        await ctx.send(embed=embed,view=VoteView())

async def setup(bot):
    await bot.add_cog(Vote(bot))