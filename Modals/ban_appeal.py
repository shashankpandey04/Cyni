import discord
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
        guild_id = self.guild_id.value
        guild_id = int(guild_id)
        settings = await self.bot.settings.find_by_id(guild_id)
        if not settings:
            return await interaction.response.send_message("Settings not found.")
        module_enabled = settings["logging_channels"]["enabled"]
        ban_appeal_channel = settings["logging_channels"]["ban_appeal_channel"]
        if not module_enabled:
            return await interaction.response.send_message("Moderation Module is not enabled.")
        if not ban_appeal_channel:
            return await interaction.response.send_message("Ban Appeal Channel is not set.")
        channel = self.bot.get_channel(ban_appeal_channel)
        if not channel:
            return await interaction.response.send_message("Ban Appeal Channel not found.")
        embed = discord.Embed(
            title="Ban Appeal",
            description=f"**Date Of Ban:** {self.date.value}\n**Reason For Ban:** {self.reason.value}\n**How You Will Change:** {self.how.value}\n**Appeal By:** {interaction.user.mention} ({interaction.user})",
            color=0x2F3136
        ).set_footer(
            text=f"User ID: {interaction.user.id}"
        )
        uid_guild_id = f"{interaction.user.id}-{guild_id}"
        previous_appeal = await self.bot.ban_appeals.find_by_id(uid_guild_id)
        if previous_appeal:
            return await interaction.response.send_message("You have already submitted a Ban Appeal.")
        await channel.send(embed=embed)
        await interaction.response.send_message("Ban Appeal submitted successfully.")
        await self.bot.ban_appeals.insert({
            "_id": uid_guild_id
        })