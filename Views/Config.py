from discord.ui import Button, View
from discord import Interaction
from discord.ext import commands
import discord
from menu import CustomModal
from utils.constants import BLANK_COLOR, RED_COLOR
from cycord.methods.DiscordModalsv2 import CyModals

class BasicConfig(View):
    def __init__(self, bot, ctx):
        super().__init__()
        self.bot = bot
        self.ctx = ctx

        self.select_menu = discord.ui.Select(
            placeholder="Select an option to configure",
            options=[
                discord.SelectOption(
                    label="Prefix",
                    description="Change the command prefix for your server",
                    emoji="🔧"
                ),
                discord.SelectOption(
                    label="Logging Channel",
                    description="Set the logging channel for moderation actions",
                    emoji="📥"
                )
            ],
            row=0
        )
        self.add_item(self.select_menu)
        self.select_menu.callback = self.select_menu_callback

    async def select_menu_callback(self, interaction: Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with this menu.",
                    color=RED_COLOR
                ),
                ephemeral=True
            )
        if self.select_menu.values[0] == "Prefix":
            await self.prefix_button_callback(interaction)
        elif self.select_menu.values[0] == "Logging Channel":
            await self.logging_channel_button(None, interaction)

    async def prefix_button_callback(self, interaction: Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with this menu.",
                    color=RED_COLOR
                ),
                ephemeral=True
            )
        prefix = "?"
        sett = await self.bot.db.servers.find_one({"guild_id": interaction.guild.id}) or {}
        if not sett.get("customization"):
            sett["customization"] = {}
        if self.bot.is_premium:
            prefix = sett.get("customization", {}).get("premium_prefix", "?")
        else:
            prefix = sett.get("customization", {}).get("prefix", "?")
        
        modal = CustomModal(
            "Enter your desired prefix",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Prefix",
                        placeholder="Enter your desired prefix here...",
                        required=True,
                        max_length=256,
                        default=prefix
                    )
                )
            ],
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return
        
        title = modal.values.get("value")
        if not title:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Title Provided",
                    description="You must provide a title.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        
        if len(title) > 256:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Title Too Long",
                    description="The title you provided is too long. Please keep it under 256 characters.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        
        if self.bot.is_premium:
            sett["customization"]["premium_prefix"] = title
        else:
            sett["customization"]["prefix"] = title

        await self.bot.db.servers.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": sett},
            upsert=True
        )
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            index=0,
            name=f"Prefix: `{sett.get('customization', {}).get('premium_prefix', '?') if self.bot.is_premium else sett.get('customization', {}).get('prefix', '?')}`",
            value=f"To change the command prefix for your server, click the button below and enter your own custom prefix!",
            inline=False
        )
        await interaction.message.edit(embed=embed)

    async def logging_channel_button(self, button: discord.ui.Button, interaction: Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with this menu.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        
class StaffToolsView(View):
    def __init__(self, bot, ctx: commands.Context):
        super().__init__()
        self.bot = bot
        self.ctx = ctx

        self.select_menu_callback = discord.ui.Select(
            placeholder="Select a staff tool to configure",
            options=[
                discord.SelectOption(
                    label="Anti-Ping Module",
                    description="Configure anti-ping settings to prevent users from pinging specific roles.",
                    emoji=f"{self.bot.emoji.get('antiping')}"
                ),
                discord.SelectOption(
                    label="Moderation Module",
                    description="Manage moderation settings and automations for your server.",
                    emoji=f"{self.bot.emoji.get('moderation')}"
                ),
                discord.SelectOption(
                    label="Staff Infraction System",
                    description="Set up and manage the staff infraction tracking system.",
                    emoji="📋"
                ),
                discord.SelectOption(
                    label="LOA Module",
                    description="Configure LOA (Leave of Absence) settings for your server.",
                    emoji=f"{self.bot.emoji.get('loa')}"
                ),
            ],
            row=0
        )
        self.add_item(self.select_menu_callback)
        self.select_menu_callback.callback = self.select_menu_callback

    async def select_menu_callback(self, interaction: Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with this menu.",
                    color=RED_COLOR
                ),
                ephemeral=True
            )
        if self.select_menu.values[0] == "Anti-Ping Module":
            await self.anti_ping_button_callback(interaction)
        elif self.select_menu.values[0] == "Moderation Module":
            await self.moderation_button_callback(interaction)
        elif self.select_menu.values[0] == "Staff Infraction System":
            await self.staff_infraction_button_callback(interaction)
        elif self.select_menu.values[0] == "LOA Module":
            await self.loa_button_callback(interaction)

    async def anti_ping_button_callback(self, interaction: Interaction, button: discord.ui.Button):
        pass

    async def moderation_button_callback(self, interaction: Interaction, button: discord.ui.Button):
        pass

    async def staff_infraction_button_callback(self, interaction: Interaction, button: discord.ui.Button):
        pass

    async def loa_button_callback(self, interaction: Interaction, button: discord.ui.Button):
        pass
    

class ServerManagementView(View):
    def __init__(self, bot, ctx: commands.Context):
        super().__init__()
        self.bot = bot
        self.ctx = ctx

        self.select_menu = discord.ui.Select(
            placeholder="Select a server management tool to configure",
            options=[
                discord.SelectOption(
                label="Server Utility Module",
                description="> Configure server utility settings for effective server management.",
                emoji=f"{self.bot.emoji.get('utility')}"
                ),
                discord.SelectOption(
                    label="Partnership Module",
                    description="> Configure partnership settings to manage server partnerships effectively.",
                    emoji=f"{self.bot.emoji.get('partnership')}"
                ),
            ],
            row=0
        )
        self.add_item(self.select_menu)
        self.select_menu.callback = self.select_menu_callback

    async def select_menu_callback(self, interaction: Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with this menu.",
                    color=RED_COLOR
                ),
                ephemeral=True
            )
        if self.select_menu.values[0] == "Server Utility Module":
            await self.server_utility_button_callback(interaction)
        elif self.select_menu.values[0] == "Partnership Module":
            await self.partnership_button_callback(interaction)

    async def server_utility_button_callback(self, interaction: Interaction, button: discord.ui.Button):
        pass

    async def partnership_button_callback(self, interaction: Interaction, button: discord.ui.Button):
        pass

class GameIntegrationView(View):
    def __init__(self, bot, ctx: commands.Context):
        super().__init__()
        self.bot = bot
        self.ctx = ctx

        self.select_menu = discord.ui.Select(
            placeholder="Select a game integration to configure",
            options=[
                discord.SelectOption(
                    label="Roblox Module",
                    description="> Configure Roblox Punishments, Shifts & Staff Roles to manage your Roblox community effectively.",
                    emoji=f"{self.bot.emoji.get('roblox')}"
                ),
                discord.SelectOption(
                    label="ER:LC Module",
                    description="> Configure ER:LC automations to manage your ER:LC community effectively.",
                    emoji=f"{self.bot.emoji.get('erlc')}"
                )
            ],
            row=0
        )
        self.add_item(self.select_menu)
        self.select_menu.callback = self.select_menu_callback

    async def select_menu_callback(self, interaction: Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with this menu.",
                    color=RED_COLOR
                ),
                ephemeral=True
            )
        elif self.select_menu.values[0] == "Roblox Module":
            await self.roblox_button_callback(interaction)
        elif self.select_menu.values[0] == "ER:LC Module":
            await self.erlc_button_callback(interaction)

    async def roblox_button_callback(self, interaction: Interaction, button: discord.ui.Button):
        pass

    async def erlc_button_callback(self, interaction: Interaction, button: discord.ui.Button):
        pass