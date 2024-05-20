import discord
import asyncio
import requests
import json
from db import mycon
class LinkRoblox(discord.ui.Modal, title="Roblox Username"):
    def __init__(self):  # initializing the modal
        super().__init__(timeout=None)  # setting the timeout of the modal to None
    username = discord.ui.TextInput(placeholder="Enter your Roblox Username", min_length=3, max_length=20, label="eg. quprgaming")  # creating a text input for the roblox username
    async def on_submit(self, interaction: discord.Interaction):
        username_value = self.username.value
        embed = discord.Embed(
            title="Roblox Username",
            description=f"Your Roblox Username is {username_value}",
            color=discord.Color.green()
        )
        embed.add_field(name="Enter this in your Roblox Profile Description", value="`cyni verification cat roblox`")
        embed.add_field(name="Note", value="Cyni will auto verify your Roblox account in a few minutes")
        await interaction.response.send_message(embed=embed)
        # wait for 1 min
        await asyncio.sleep(60)
        api_url = "https://users.roblox.com/v1/usernames/users"
        payload = {"usernames": [username_value], "excludeBannedUsers": True}
        response = requests.post(api_url, json=payload)
        data = response.json().get("data", [])
        if response.status_code == 200 and data:
            try:
                userid = data[0]["id"]
                api_url = f"https://users.roblox.com/v1/users/{userid}"
                response = requests.get(api_url)
                data = response.json()

                if response.status_code == 200:
                    user_description = data.get("description", "")
                    if "cyni verification cat roblox" in user_description:
                        await interaction.followup.send("Your Roblox account has been verified")
                        mycursor = mycon.cursor()
                        mycursor.execute("INSERT into roblox_user (user_id, username) VALUES (%s, %s)", (interaction.user.id, username_value))
                        mycon.commit()
                        mycursor.close()
                    else:
                        await interaction.followup.send("Your Roblox account has not been verified")
            except Exception as e:
                await interaction.followup.send("An error occurred while verifying your Roblox account")
                print(e)
        else:
            await interaction.followup.send("Your Roblox account has not been verified")
