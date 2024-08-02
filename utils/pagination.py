import discord
from discord.ext import commands

class Pagination(discord.ui.View):
    def __init__(self, bot: commands.Bot, user_id: int, embeds, views):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.embeds = embeds
        self.views = views
        self.current = 0

        self.previous_button = discord.ui.Button(label="<", style=discord.ButtonStyle.secondary, row=4)
        self.previous_button.callback = self.previous

        self.next_button = discord.ui.Button(label=">", style=discord.ButtonStyle.secondary, row=4)
        self.next_button.callback = self.next

        self.add_item(self.previous_button)
        self.add_item(self.next_button)
        self.update_buttons_state()
        self.update_view_items()

    def update_buttons_state(self):
        """Update the state of the pagination buttons."""
        self.previous_button.disabled = self.current == 0
        self.next_button.disabled = self.current == len(self.embeds) - 1

    def update_view_items(self):
        """Update the items from the current view."""
        self.clear_items()
        self.add_item(self.previous_button)
        self.add_item(self.next_button)
        
        for item in self.views[self.current].children:
            self.add_item(item)

    async def previous(self, interaction: discord.Interaction):
        """Handle the previous button click."""
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not allowed to interact with this button.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        if self.current > 0:
            self.current -= 1
            self.update_buttons_state()
            self.update_view_items()
            await self.update_message(interaction)

    async def next(self, interaction: discord.Interaction):
        """Handle the next button click."""
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not allowed to interact with this button.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        if self.current < len(self.embeds) - 1:
            self.current += 1
            self.update_buttons_state()
            self.update_view_items()
            await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        """Update the message with the new embed and view."""
        embed = self.embeds[self.current]
        await interaction.response.edit_message(embed=embed, view=self)
