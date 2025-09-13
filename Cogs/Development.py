from cycord.methods.DiscordModalsv2 import CyModals
import discord
from discord import app_commands
from discord.ext import commands

class DevelopmentView(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Click Me", style=discord.ButtonStyle.primary, custom_id="development_view:click_me")
    async def click_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CyModals(
            "Bug Report",
            [
                {
                    "type": "user",
                    "custom_id": "bug_reporter",
                    "label": "Who is reporting?",
                    "description": "Select the reporter from your server",
                    "placeholder": "Choose a user...",
                },
                {
                    "type": "text",
                    "custom_id": "bug_explanation",
                    "label": "Explain the bug",
                    "description": "Give as much detail as possible",
                    "style": discord.TextStyle.paragraph,
                    "placeholder": "Write explanation here...",
                    "required": True,
                    "min_length": 20,
                    "max_length": 1000,
                },
            ]
        )
        await interaction.response.send_modal(modal)
        await modal.wait()

        self.bot.logger.info(f"Modal submitted with values: {modal.values}")
        await interaction.followup.send(
            f"Thank you {interaction.user.mention} for your report! We will look into it.",
            ephemeral=True
        )


class Development(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="testmodal",
        description="Test a modal dialog",
        extras={
            "category": "Development"
        }
    )
    @commands.is_owner()
    async def testmodal(self, ctx: commands.Context):
        """Test a modal dialog interaction."""
        view = DevelopmentView(self.bot)
        await ctx.send("Click the button to report a bug:", view=view)

async def setup(bot):
    await bot.add_cog(Development(bot))