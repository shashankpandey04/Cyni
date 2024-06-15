import discord
from utils import submit_ban_appeal
from discord.ext import commands

class BanAppealModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Ban Appeal", timeout=None)
        self.bot = bot

    date = discord.ui.TextInput(
        placeholder="Date Of Ban", min_length=3, max_length=20, label="Example: 12/12/2021"
    ) 
    reason = discord.ui.TextInput(
        placeholder="Reason For Ban", min_length=3, max_length=20, label="Example: Spamming"
    )
    how = discord.ui.TextInput(
        placeholder="How You Will Change", min_length=3, max_length=20, label="Example: I will not spam again"
    )
    guild_id = discord.ui.TextInput(
        placeholder="Guild ID", min_length=3, max_length=20, label="Example: 1234567890"
    )  
    
    async def on_submit(self, interaction: discord.Interaction):
        await submit_ban_appeal(
            self.bot, interaction, self.date.value, self.reason.value, self.how.value, self.guild_id.value
        )