import discord
from db import mycon

class Prefix(discord.ui.Modal,title="Edit Prefix"):
    def __init__(self): #initializing the modal
        super().__init__(timeout=None) #setting the timeout of the modal to None
    quota = discord.ui.TextInput(placeholder="Enter the Prefix",min_length=1,max_length=5,label="Minimum 1") #creating a text input for the roblox username
    async def on_submit(self,interaction:discord.Interaction):
        cursor = mycon.cursor()
        cursor.execute("UPDATE server_config SET prefix = %s WHERE guild_id = %s", (self.quota.value,interaction.guild.id))
        mycon.commit()
        cursor.close()
        await interaction.response.send_message("Message Quota has been saved.",ephemeral=True)
