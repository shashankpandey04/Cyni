from discord.ui import Button, View
from discord import Interaction, ButtonStyle
import discord
from menu import CustomModal
from utils.constants import BLANK_COLOR

class ReactionBoard(View):
    def __init__(self, bot, ctx):
        super().__init__(timeout=90)
        self.bot = bot
        self.ctx = ctx
        self.doc = {}

    @discord.ui.ChannelSelect(
        placeholder="Select a channel...",
        min_values=1,
        max_values=1,
        channel_types=[discord.ChannelType.text]
    )
    async def channel_select(self, interaction: Interaction, select):
        channel = select.values[0]
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name="Channel", value=f"<#{channel.id}>", inline=False)
        if 'reaction_board' not in self.doc:
            self.doc['reaction_board'] = {}
        reaction_board = self.doc.setdefault('reaction_board', {})
        reaction_board.update({
            'channel_id': channel.id,
            'reactions_required': reaction_board.get('reactions_required', 0)
        })
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.Button(label="Set Reactions Required", style=ButtonStyle.secondary)
    async def set_reactions(self, button: Button, interaction: Interaction):
        modal = CustomModal(
            "Set Reactions Required",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Reactions Required",
                        placeholder="The total number of reactions required",
                        style=discord.TextStyle.short,
                        required=True,
                        max_length=256,
                    )
                )
            ],
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return
        
        number = modal.values.get("value")
        if not number or not number.isdigit() or int(number) < 1:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Title Provided",
                    description="You must provide a title.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        number = int(number)
        embed = interaction.message.embeds[0]
        embed.set_field_at(1, name="Reactions Required", value=str(number), inline=False)
        if 'reaction_board' not in self.doc:
            self.doc['reaction_board'] = {}
        reaction_board = self.doc.setdefault('reaction_board', {})
        reaction_board.update({
            'channel_id': reaction_board.get('channel_id', None),
            'reactions_required': number
        })
        await interaction.followup.send(
            embed=discord.Embed(
                title="Reactions Required Set",
                description=f"Reactions required set to {number}.",
                color=BLANK_COLOR
            ), ephemeral=True
        )
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.Button(label="Confirm", style=ButtonStyle.success)
    async def confirm(self, button: Button, interaction: Interaction):
        if 'reaction_board' not in self.doc or \
           'channel_id' not in self.doc['reaction_board'] or \
           'reactions_required' not in self.doc['reaction_board']:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Incomplete Configuration",
                    description="Please ensure both channel and reactions required are set.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Configuration Confirmed",
                description="Reaction board configuration has been saved.",
                color=BLANK_COLOR
            ), ephemeral=True
        )
        self.bot.settings.update_one(
            {'_id': self.ctx.guild.id},
            {'$set': {'reaction_board': self.doc['reaction_board']}},
            upsert=True
        )
        self.stop()
        self.clear_items()
        await interaction.edit_original_response(view=None)