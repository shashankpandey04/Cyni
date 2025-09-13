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
                    "type": "channel",
                    "custom_id": "bug_channel",
                    "label": "Where is the bug?",
                    "description": "Select the channel where the bug was found",
                    "placeholder": "Choose a channel...",
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

        modal_values = modal.values
        channel_ids = modal_values.get("bug_channel", [])
        explanation = modal_values.get("bug_explanation", "No explanation provided")

        # Convert channel ID to Discord channel object
        if channel_ids:
            channel_id = int(channel_ids[0])  # Get the first selected channel
            channel = interaction.guild.get_channel(channel_id)
            
            if channel:
                channel_mention = channel.mention
                channel_name = channel.name
            else:
                channel_mention = f"<#{channel_id}>"
                channel_name = f"Unknown Channel (ID: {channel_id})"
        else:
            channel_mention = "No channel selected"
            channel_name = "None"

        self.bot.logger.info(f"Modal submitted with channel: {channel_name} ({channel_ids}), explanation: {explanation}")
        
        embed = discord.Embed(
            title="🐛 Bug Report Received",
            description="Thank you for reporting this bug!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📍 Channel",
            value=channel_mention,
            inline=True
        )
        
        embed.add_field(
            name="📝 Report",
            value=explanation[:500] + "..." if len(explanation) > 500 else explanation,
            inline=False
        )
        
        embed.set_footer(text=f"Reported by {interaction.user.display_name}")
        
        await interaction.followup.send(
            embed=embed,
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