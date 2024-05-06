import discord
from discord.ext import commands
from menu import VoteView

class Vote(commands.Cog):
    def __init__ (self,bot):
        self.bot = bot
    
    @commands.hybrid_command(name="vote", aliases=["v"], brief="Vote for Cyni", description="Vote for Cyni on top.gg", usage="vote", help="Vote for Cyni on top.gg to help support the bot.")
    async def vote(self,ctx):
        embed = discord.Embed(title="Vote Cyni!")
        await ctx.send(embed=embed,view=VoteView())

async def setup(bot):
    await bot.add_cog(Vote(bot))