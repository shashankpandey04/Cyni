import discord
from discord.ext import commands
import aiohttp
from cyni import on_command_error

from utils import roblox_discord_timestamp

class Roblox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.hybrid_group(
        name="roblox",
        aliases=["rblx"],
        brief="Roblox related commands",
        description="Roblox related commands",
        usage="roblox",
        help="Roblox related commands"
    )
    async def roblox(self, ctx):
        pass

    @roblox.command()
    async def search(self, ctx, user: str):
        '''Search for a Roblox User'''
        async with aiohttp.ClientSession() as session:
            try:
                if user.isdigit():
                    api_url = f"https://users.roblox.com/v1/users/{user}"
                    avatar_api_url = f"https://www.roblox.com/avatar-thumbnails?params=[{{userId:{user}}}]"

                    async with session.get(avatar_api_url) as avatar_response:
                        avatar_data = await avatar_response.json()
                        thumbnail_url = avatar_data[0]["thumbnailUrl"]

                    async with session.get(api_url) as user_response:
                        if user_response.status_code == 200:
                            data = await user_response.json()
                            embed = discord.Embed(title="User Info", color=0x00ff00)
                            embed.add_field(name="User ID", value=data["id"], inline=False)
                            embed.add_field(name="Username", value=data["name"], inline=False)
                            embed.add_field(name="Display Name", value=data["displayName"], inline=False)
                            embed.add_field(name="Description", value=data["description"], inline=False)
                            embed.set_thumbnail(url=thumbnail_url)
                            embed.add_field(name="Is Banned", value=data["isBanned"], inline=False)
                            embed.add_field(name="Has Verified Badge", value=data["hasVerifiedBadge"], inline=False)
                            embed.add_field(name="Created", value=roblox_discord_timestamp(data['created']), inline=False)
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send("Error fetching user data from Roblox API.")
                else:
                    api_url = "https://users.roblox.com/v1/usernames/users"
                    payload = {"usernames": [user], "excludeBannedUsers": True}
                    
                    async with session.post(api_url, json=payload) as response:
                        if response.status_code == 200:
                            data = await response.json()
                            user_data = data.get("data", [])
                            if not user_data:
                                await ctx.send("User not found.")
                                return

                            user_id = user_data[0]["id"]
                            
                            user_api_url = f"https://users.roblox.com/v1/users/{user_id}"
                            avatar_api_url = f"https://www.roblox.com/avatar-thumbnails?params=[{{userId:{user_id}}}]"
                            
                            async with session.get(avatar_api_url) as avatar_response:
                                if avatar_response.status_code == 200:
                                    avatar_data = await avatar_response.json()
                                    thumbnail_url = avatar_data[0]["thumbnailUrl"]
                                else:
                                    await ctx.send("Error fetching avatar data.")
                                    return
                            
                            async with session.get(user_api_url) as user_response:
                                if user_response.status_code == 200:
                                    data = await user_response.json()
                                    embed = discord.Embed(
                                        title="Roblox Info", 
                                        color=0x2F3136
                                    ).add_field(
                                        name="User ID", 
                                        value=data["id"], 
                                        inline=False
                                    ).add_field(
                                        name="Username", 
                                        value=data["name"], 
                                        inline=False
                                    ).add_field(
                                        name="Display Name",
                                        value=data["displayName"],
                                        inline=False
                                    ).add_field(
                                        name="Description",
                                        value=data["description"],
                                        inline=False
                                    ).set_thumbnail(
                                        url=thumbnail_url
                                    ).add_field(
                                        name="Is Banned", 
                                        value=data["isBanned"], 
                                        inline=False
                                    ).add_field(
                                        name="Has Verified Badge",
                                        value=data["hasVerifiedBadge"],
                                        inline=False
                                    ).add_field(
                                        name="Created", 
                                        value=roblox_discord_timestamp(data['created']), 
                                        inline=False
                                    )
                                    await ctx.send(embed=embed)
                                else:
                                    await ctx.send("Error fetching user data from Roblox API.")
                        else:
                            await ctx.send("Error: User not found or API request failed.")
            except Exception as e:
                await on_command_error(ctx, e)

async def setup(bot):
    await bot.add_cog(Roblox(bot))
