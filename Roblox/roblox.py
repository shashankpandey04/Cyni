import discord
from discord.ext import commands
import requests
from cyni import on_command_error

from Modals.roblox_username import LinkRoblox

from utils import roblox_discord_timestamp
class Roblox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.hybrid_group(name="roblox", aliases=["rblx"], brief="Roblox related commands", description="Roblox related commands", usage="roblox", help="Roblox related commands")
    async def roblox(self, ctx):
        pass

    @roblox.command()
    async def search(self,ctx,user:str):
        '''Search for a Roblox User'''
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
                    embed.add_field(name="Created", value=roblox_discord_timestamp(data['created']), inline=False)
                    await ctx.send(embed=embed)
            else:
                api_url = "https://users.roblox.com/v1/usernames/users"
                payload = {"usernames": [user], "excludeBannedUsers": True}
                
                response = requests.post(api_url, json=payload)
                
                if response.status_code == 200:
                    try:
                        data = response.json().get("data", [])
                        if not data:
                            await ctx.send("User not found.")
                            return
                        
                        user_data = data[0]
                        user_id = user_data["id"]
                        
                        api_url = f"https://users.roblox.com/v1/users/{user_id}"
                        avatar_api_url = f"https://www.roblox.com/avatar-thumbnails?params=[{{userId:{user_id}}}]"
                        
                        response = requests.get(avatar_api_url)
                        if response.status_code == 200:
                            try:
                                avatar_data = response.json()[0]
                                thumbnail_url = avatar_data["thumbnailUrl"]
                            except (ValueError, KeyError, IndexError):
                                await ctx.send("Error parsing avatar data.")
                                return
                        else:
                            await ctx.send("Error fetching avatar data.")
                            return
                        
                        response = requests.get(api_url)
                        if response.status_code == 200:
                            try:
                                data = response.json()
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
                            except (ValueError, KeyError) as e:
                                await ctx.send(f"Error parsing user data: {e}")
                        else:
                            await ctx.send("Error fetching user data from Roblox API.")
                    except (ValueError, KeyError) as e:
                        await ctx.send(f"Error parsing response: {e}")
                else:
                    await ctx.send("Error: User not found or API request failed.")

        except Exception as e:
            await on_command_error(ctx,e)

    #@roblox.command()
    #async def link(self,interaction:discord.Interaction):
    #    '''Link Roblox Account'''
    #    user_id = interaction.author.id
    #    cursor = mycon.cursor()
    #    cursor.execute("SELECT * FROM roblox_user WHERE user_id = %s", (user_id,))
    #    roblox_user = cursor.fetchone()
    #    if roblox_user:
    #        await interaction.response.send_message("❌ You have already linked a Roblox account.")
    #    else:
    #        await interaction.response.send_modal(LinkRoblox())

async def setup(bot):
   await bot.add_cog(Roblox(bot))