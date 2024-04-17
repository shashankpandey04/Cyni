import discord
from discord.ext import commands
import requests
from cyni import on_command_error

class Roblox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def search(self,ctx,user:str):
        try:
            if user.isdigit():
                api_url = f"https://users.roblox.com/v1/users/{user}"
                avatar_api_url = f"https://www.roblox.com/avatar-thumbnails?params=[{{userId:{user}}}]"
                response = requests.get(avatar_api_url)
                avatar_data = response.json()[0]
                thumbnail_url = avatar_data["thumbnailUrl"]
                response = requests.get(api_url)
                if response.status_code == 200:
                    data = response.json()
                    embed = discord.Embed(title="User Info", color=0x00ff00)
                    embed.add_field(name="User ID", value=data["id"], inline=False)
                    embed.add_field(name="Username", value=data["name"], inline=False)
                    embed.add_field(name="Display Name",value=data["displayName"],inline=False)
                    embed.add_field(name="Description",value=data["description"],inline=False)
                    embed.set_thumbnail(url=thumbnail_url)
                    embed.add_field(name="Is Banned", value=data["isBanned"], inline=False)
                    embed.add_field(name="Has Verified Badge",value=data["hasVerifiedBadge"],inline=False)
                    embed.add_field(name="Created", value=data["created"], inline=False)
                    await ctx.send(embed=embed)
            else:
                api_url = "https://users.roblox.com/v1/usernames/users"
                payload = {"usernames": [user], "excludeBannedUsers": True}
                response = requests.post(api_url, json=payload)
                if response.status_code == 200:
                    data = response.json()["data"][0]
                    embed = discord.Embed(title="User Info", color=0x00ff00)
                    embed.add_field(name="Username",value=data["requestedUsername"],inline=False)
                    embed.add_field(name="Display Name",value=data["displayName"],inline=False)
                    embed.add_field(name="Verified Badge",value=data["hasVerifiedBadge"],inline=False)
                    embed.add_field(name="User ID", value=data["id"], inline=False)
                    await ctx.send(embed=embed)
        except Exception as e:
            await on_command_error(ctx,e)

async def setup(bot):
   await bot.add_cog(Roblox(bot))