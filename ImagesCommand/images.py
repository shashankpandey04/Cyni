import discord
from discord.ext import commands
import requests
from cyni import on_command_error
from discord import app_commands

class Images(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} loaded cog: Images')

    @commands.command()
    async def doge(self,ctx):
        '''Get Doge Image'''
        try:
            response = requests.get("https://api.thedogapi.com/v1/images/search")
            data = response.json()
            image_url = data[0]["url"]
            embed = discord.Embed(title="Random Dog Image", color=discord.Color.random())
            embed.set_image(url=image_url)
            await ctx.send(embed=embed)
        except Exception as e:
            on_command_error(ctx,e)
    
    @commands.command()
    async def birb(self,ctx):
        '''Get Random Bird Image'''
        try:
            response = requests.get("https://birbapi.astrobirb.dev/birb")
            data = response.json()
            image_url = data["image_url"]
            embed = discord.Embed(title="Random Bird Image", color=discord.Color.random())
            embed.set_image(url=image_url)
            await ctx.send(embed=embed)
        except Exception as e:
            on_command_error(ctx,e)
    
    @commands.command()
    async def cat(self,ctx):
        try:
            '''Get Random Cat Image'''
            response = requests.get("https://api.thecatapi.com/v1/images/search")
            data = response.json()
            image_url = data[0]["url"]
            embed = discord.Embed(title="Random Cat Image", color=discord.Color.random())
            embed.set_image(url=image_url)
            await ctx.send(embed=embed)
        except Exception as e:
            on_command_error(ctx,e)

async def setup(bot):
   await bot.add_cog(Images(bot))