import discord
from discord.ext import commands
from utils import fetch_random_joke

class Jokes(commands.Cog):
    def __init__ (self,bot):
        self.bot = bot

    @commands.hybrid_command(name="joke", aliases=["j"], brief="Get a random joke", description="Get a random joke from the internet.", usage="joke", help="Get a random joke from the internet.")
    async def joke(self,ctx):
        joke = fetch_random_joke()
        await ctx.send(joke)

async def setup(bot):
    await bot.add_cog(Jokes(bot))