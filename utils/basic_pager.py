import discord
from discord.ext import commands

class BasicPager(discord.ui.View):
    def __init__(self, user_id: int, embeds):
        super().__init__()
        self.user_id = user_id
        self.embeds = embeds
        self.current = 0

        # Create pager buttons
        self.first_button = discord.ui.Button(label="⏮️", style=discord.ButtonStyle.secondary, row=0)
        self.first_button.callback = self.go_first

        self.prev_button = discord.ui.Button(label="◀️", style=discord.ButtonStyle.secondary, row=0)
        self.prev_button.callback = self.go_prev

        self.next_button = discord.ui.Button(label="▶️", style=discord.ButtonStyle.secondary, row=0)
        self.next_button.callback = self.go_next

        self.last_button = discord.ui.Button(label="⏭️", style=discord.ButtonStyle.secondary, row=0)
        self.last_button.callback = self.go_last

        self.add_item(self.first_button)
        self.add_item(self.prev_button)
        self.add_item(self.next_button)
        self.add_item(self.last_button)

        self.update_buttons()

    def update_buttons(self):
        # Disable buttons at bounds
        self.first_button.disabled = self.current == 0
        self.prev_button.disabled = self.current == 0
        self.next_button.disabled = self.current == len(self.embeds) - 1
        self.last_button.disabled = self.current == len(self.embeds) - 1

    async def go_first(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await self.not_permitted(interaction)
        self.current = 0
        self.update_buttons()
        await self.update_message(interaction)

    async def go_prev(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await self.not_permitted(interaction)
        if self.current > 0:
            self.current -= 1
        self.update_buttons()
        await self.update_message(interaction)

    async def go_next(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await self.not_permitted(interaction)
        if self.current < len(self.embeds) - 1:
            self.current += 1
        self.update_buttons()
        await self.update_message(interaction)

    async def go_last(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await self.not_permitted(interaction)
        self.current = len(self.embeds) - 1
        self.update_buttons()
        await self.update_message(interaction)

    async def not_permitted(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Not Permitted",
                description="You are not allowed to interact with this button.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )

    async def update_message(self, interaction: discord.Interaction):
        embed = self.embeds[self.current]
        await interaction.response.edit_message(embed=embed, view=self)
