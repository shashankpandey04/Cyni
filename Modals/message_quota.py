import discord
from utils import save_message_quota

class MessageQuota(discord.ui.Modal,title="Edit Message Quota"):
    def __init__(self): #initializing the modal
        super().__init__(timeout=None) #setting the timeout of the modal to None
    quota = discord.ui.TextInput(placeholder="Enter the Message Quota",min_length=3,max_length=20,label="Minimum 100") #creating a text input for the roblox username
    
    async def on_submit(self,interaction:discord.Interaction):
        save_message_quota(interaction.guild.id,self.quota.value)
        await interaction.response.send_message("Message Quota has been saved.",ephemeral=True)
