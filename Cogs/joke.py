import discord
from discord.ext import commands
from utils import fetch_random_joke

class Jokes(commands.Cog):
    def __init__ (self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} loaded Jokes Cog.")
    
    @commands.command()
    async def joke(self,ctx):
        joke = fetch_random_joke()
        await ctx.send(joke)

async def setup(bot):
    await bot.add_cog(Jokes(bot))