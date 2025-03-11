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

        # Create pagination buttons
        self.previous_button = discord.ui.Button(label="<", style=discord.ButtonStyle.secondary, row=4)
        self.previous_button.callback = self.previous

        self.page_selector_button = discord.ui.Button(
            label=f"{self.get_embed_title(self.current)}",
            style=discord.ButtonStyle.secondary,
            row=4,
            disabled=True
        )
        self.page_selector_button.callback = self.show_page_selector

        self.next_button = discord.ui.Button(label=">", style=discord.ButtonStyle.secondary, row=4)
        self.next_button.callback = self.next

        self.add_item(self.previous_button)
        self.add_item(self.page_selector_button)
        self.add_item(self.next_button)
        
        self.update_view_items()

    def update_view_items(self):
        """Update the items from the current view."""
        self.clear_items()
        self.page_selector_button.label = self.get_embed_title(self.current)
        self.add_item(self.previous_button)
        self.add_item(self.page_selector_button)
        self.add_item(self.next_button)

        for item in self.views[self.current].children:
            self.add_item(item)

    def get_embed_title(self, embed_index):
        """Get title from embed or generate a default if title is not present."""
        embed = self.embeds[embed_index]
        if embed.title:
            return embed.title
        return f"Page {embed_index + 1}"

    async def previous(self, interaction: discord.Interaction):
        """Handle the previous button click with circular navigation."""
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not allowed to interact with this button.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        
        if self.current == 0:
            self.current = len(self.embeds) - 1
        else:
            self.current -= 1
            
        self.update_view_items()
        await self.update_message(interaction)

    async def next(self, interaction: discord.Interaction):
        """Handle the next button click with circular navigation."""
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not allowed to interact with this button.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        if self.current == len(self.embeds) - 1:
            self.current = 0
        else:
            self.current += 1
            
        self.update_view_items()
        await self.update_message(interaction)
    
    async def show_page_selector(self, interaction: discord.Interaction):
        """Show a dropdown to select a specific page."""
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not allowed to interact with this button.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        view = discord.ui.View()

        options = []
        for i in range(len(self.embeds)):
            title = self.get_embed_title(i)
            display_title = title[:100] + "..." if len(title) > 100 else title
            options.append(
                discord.SelectOption(
                    label=display_title,
                    value=str(i),
                    default=i == self.current
                )
            )
        
        select = discord.ui.Select(
            placeholder="Select a page",
            min_values=1,
            max_values=1,
            options=options
        )
        
        async def select_callback(select_interaction: discord.Interaction):
            selected_page = int(select_interaction.data["values"][0])
            self.current = selected_page
            self.update_view_items()
            await select_interaction.response.edit_message(
                embed=self.embeds[self.current], 
                view=self
            )
        
        select.callback = select_callback
        view.add_item(select)
        
        current_title = self.get_embed_title(self.current)
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Page Selection",
                description=f"Currently on: **{current_title}**\nSelect a page to navigate:",
                color=discord.Color.blue()
            ),
            view=view,
            ephemeral=True
        )

    async def update_message(self, interaction: discord.Interaction):
        """Update the message with the new embed and view."""
        embed = self.embeds[self.current]
        await interaction.response.edit_message(embed=embed, view=self)