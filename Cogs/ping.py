import discord
from discord.ext import commands
import time
import requests
import psutil
from cyni import dbstatus, on_command_error
from utils import fetch_random_joke

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} loaded cog: Ping')

    @commands.hybrid_command(name="ping", aliases=["pong","p"], brief="Check the bot's latency", description="Check the bot's latency and uptime.", usage="ping", help="Check the bot's latency and uptime. The bot will respond with its latency in milliseconds, uptime, and database status.")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        db = dbstatus()
        support_server_id = 1152949579407442050
        support_server = self.bot.get_guild(support_server_id)
        database_emoji = discord.utils.get(support_server.emojis, id=1215565017718587422)
        angle_right = discord.utils.get(support_server.emojis,id=1215565088589877299)
        uptime_seconds = time.time() - self.bot.start_time
        uptime_string = time.strftime('%Hh %Mm %Ss', time.gmtime(uptime_seconds))
        embed = discord.Embed(title='Bot Ping', color=0x00FF00)
        embed.add_field(name=f'{angle_right} 🟢 Pong!', value=f"{latency}ms", inline=True)
        embed.add_field(name=f'{angle_right} Uptime', value=uptime_string, inline=True)
        embed.add_field(name=f"{database_emoji} Database Status", value=db, inline=True)
        embed.add_field(name=f"{angle_right} Bot Version", value="6.2.0", inline=True)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        await ctx.channel.send(embed=embed)

async def setup(bot):
   await bot.add_cog(Ping(bot))