import discord
from discord.ext import commands
from utils.constants import BLANK_COLOR
import aiohttp

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="joke",
        extras={
            "category": "Fun"
        }
    )
    async def joke(self, ctx):
        """
        Get a random joke.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("https://official-joke-api.appspot.com/random_joke") as response:
                data = await response.json()
                await ctx.send(f"{data['setup']}\n{data['punchline']}")

    @commands.hybrid_command(
        name="dog",
        extras={
            "category": "Fun"
        }
    )
    async def dog(self, ctx):
        """
        Get a random dog image.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as response:
                data = await response.json()
                await ctx.send(
                    embed=discord.Embed(
                        title="Dog",
                        color=discord.Color.blurple()
                    ).set_image(
                        url=data["message"]
                    )
                )

    @commands.hybrid_command(
        name="cat",
        extras={
            "category": "Fun"
        }
    )
    async def cat(self, ctx):
        """
        Get a random cat image.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as response:
                data = await response.json()
                await ctx.send(
                    embed=discord.Embed(
                        title="Cat",
                        color=discord.Color.blurple()
                    ).set_image(
                        url=data[0]["url"]
                    )
                )

    @commands.hybrid_command(
        name="meow",
        extras={
            "category": "Fun"
        }
    )
    async def meow(self, ctx):
        """
        Get a random Cat Fact.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meowfacts.herokuapp.com/") as response:
                data = await response.json()
                await ctx.send(
                    embed=discord.Embed(
                        title=data["data"][0],
                        color=BLANK_COLOR
                    )
                )

async def setup(bot):
    await bot.add_cog(Fun(bot))