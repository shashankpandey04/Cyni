import discord
from discord.ext import commands
from discord import app_commands
import time
import requests
import psutil
from cyni import dbstatus, on_general_error
from utils import fetch_random_joke

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} loaded cog: Ping')

    @commands.command()
    async def ping(self, ctx):
        db = dbstatus()
        latency = round(self.bot.latency * 1000) 
        support_server_id = 1152949579407442050
        support_server = self.bot.get_guild(support_server_id)
        database_emoji = discord.utils.get(support_server.emojis, id=1210273731369373798)
        start_time_birb = time.time()
        response_birb = requests.get("https://birbapi.astrobirb.dev/birb")
        birb_api_latency = round((time.time() - start_time_birb) * 1000)
        start_time_joke = time.time()
        response_joke = requests.get("https://official-joke-api.appspot.com/jokes/random")
        joke_api_latency = round((time.time() - start_time_joke) * 1000)
        average_api_latency = (birb_api_latency + joke_api_latency) / 2
        ram_usage = psutil.virtual_memory().percent
        uptime_seconds = time.time() - self.bot.start_time  # Access bot start time via `self.bot`
        uptime_string = time.strftime('%Hh %Mm %Ss', time.gmtime(uptime_seconds))
        embed = discord.Embed(title='Bot Ping', color=0x00FF00)
        embed.add_field(name='🟢 Pong!', value=f"{latency}ms", inline=True)
        embed.add_field(name='Uptime', value=uptime_string, inline=True)
        embed.add_field(name='API Latency', value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name='External API Latency', value=f"{average_api_latency}ms", inline=True)
        embed.add_field(name='System RAM Usage', value=f"{ram_usage}%", inline=True)
        embed.add_field(name=f"{database_emoji} Database Status", value=db, inline=True)
        embed.add_field(name="Bot Version", value="6.2.0", inline=True)
        embed.set_thumbnail(url=self.bot.user.avatar.url)  # Access bot avatar via `self.bot`
        await ctx.send(embed=embed)
        
    @commands.command()
    async def joke(self, ctx):
        try:
            joke = fetch_random_joke()
            await ctx.channel.send(joke)
        except Exception as e:
            on_general_error(ctx,e)

async def setup(bot):
   await bot.add_cog(Ping(bot))