import discord
from discord.ext import commands
import aiohttp
from cyni import on_command_error
from discord import app_commands

class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} loaded cog: Images')

    @commands.hybrid_command(
        name="doge",
        aliases=["dog"],
        brief="Get a random dog image",
        description="Get a random dog image from the internet.",
        usage="doge",
        help="Get a random dog image from the internet."
    )
    async def doge(self, ctx):
        '''Get Doge Image'''
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://api.thedogapi.com/v1/images/search") as response:
                    data = await response.json()
                    image_url = data[0]["url"]
                    embed = discord.Embed(title="Random Dog Image", color=0x2F3136)
                    embed.set_image(url=image_url)
                    await ctx.send(embed=embed)
            except Exception as e:
                await on_command_error(ctx, e)

    @commands.hybrid_command(
        name="cat",
        aliases=["kitty"],
        brief="Get a random cat image",
        description="Get a random cat image from the internet.",
        usage="cat",
        help="Get a random cat image from the internet."
    )
    async def cat(self, ctx):
        '''Get Random Cat Image'''
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://api.thecatapi.com/v1/images/search") as response:
                    data = await response.json()
                    image_url = data[0]["url"]
                    embed = discord.Embed(title="Random Cat Image", color=0x2F3136)
                    embed.set_image(url=image_url)
                    await ctx.send(embed=embed)
            except Exception as e:
                await on_command_error(ctx, e)

async def setup(bot):
    await bot.add_cog(Images(bot))
