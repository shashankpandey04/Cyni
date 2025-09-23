from discord.ui import Button, View
from discord import Interaction
from discord.ext import commands
import discord
from menu import CustomModal
from utils.constants import BLANK_COLOR, RED_COLOR
from cycord.methods.DiscordModalsv2 import CyModals

class LandingEmbedView(View):
    def __init__(self, bot, ctx, sett):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.sett = sett

        self.select_menu = discord.ui.Select(
            placeholder="Select a configuration module",
            options=[
                discord.SelectOption(
                    label="Staff Tools",
                    description="Configure staff-related tools and settings",
                    emoji="🛡️"
                ),
                discord.SelectOption(
                    label="Server Management",
                    description="Manage server-wide settings and features",
                    emoji="🛠️"
                ),
                discord.SelectOption(
                    label="Game Integrations",
                    description="Set up and manage game-related integrations",
                    emoji="🎮"
                )
            ],
        )
        self.add_item(self.select_menu)
        self.select_menu.callback = self.select_menu_callback

        self.prefix = self.sett.get('customization', {})
        if self.bot.is_premium:
            self.prefix = self.prefix.get('premium_prefix', '?')
        else:
            self.prefix = self.prefix.get('prefix', '?')

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
        if self.select_menu.values[0] == "Staff Tools":
            embed = discord.Embed(
                title="Staff Tools Configuration",
                description=(
                    "Overview of staff-related tools and settings.\n\n"
                    f"> - {self.bot.emoji.get('antiping')} Anti-Ping Module: {'**Enabled**' if self.sett.get('anti_ping_module', {}).get('enabled', False) else '**Disabled**'}\n"
                    f"> - {self.bot.emoji.get('moderation')} Moderation Module: {'**Enabled**' if self.sett.get('moderation_module', {}).get('enabled', False) else '**Disabled**'}\n"
                    f"> - 📝 Staff Infraction Module: {'**Enabled**' if self.sett.get('staff_management', {}).get('enabled', False) else '**Disabled**'}\n"
                    f"> - {self.bot.emoji.get('loa')} LOA Module: {'**Enabled**' if self.sett.get('leave_of_absence', {}).get('enabled', False) else '**Disabled**'}\n\n"
                ),
                color=BLANK_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.select_menu.values[0] == "Server Management":
            embed = discord.Embed(
                title="Server Management Configuration",
                description=(
                    "Overview of server-wide settings and features.\n\n"
                    f"> - {self.bot.emoji.get('utility')} Prefix: {'`' + self.prefix + '`'}\n"
                    f"> - {self.bot.emoji.get('partnership')} Partnership Module: {'**Enabled**' if self.sett.get('partnership_module', {}).get('enabled', False) else '**Disabled**'}\n\n"
                ),
                color=BLANK_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.select_menu.values[0] == "Game Integrations":
            embed = discord.Embed(
                title="Game Integrations Configuration",
                description=(
                    "Overview of game-related integrations.\n\n"
                    f"{self.bot.emoji.get('roblox')} Roblox Management\n"
                    f">  - Staff Roles: {'**Configured**' if self.sett.get('roblox', {}).get('staff_roles', False) else '**Not Configured**'}\n"
                    f">  - Shift Module: {'**Configured**' if self.sett.get('roblox', {}).get('shift_module',{}).get('channel', False) else '**Not Configured**'}\n"
                    f">  - Punishment Module: {'**Configured**' if self.sett.get('roblox', {}).get('punishments',{}).get('enabled', False) else '**Not Configured**'}\n\n"
                    f"{self.bot.emoji.get('prc')} ER:LC Automations\n"
                    f">  - Kill Logs: {'**Configured**' if self.sett.get('erlc', {}).get('kill_logs_channel', False) else '**Not Configured**'}\n"
                    f">  - Join Logs: {'**Configured**' if self.sett.get('erlc', {}).get('join_logs_channel', False) else '**Not Configured**'}\n"
                    f">  - Discord Checks: {'**Enabled**' if self.sett.get('erlc', {}).get('discord_check_log_channel', False) else '**Disabled**'}\n"
                    f">  - Auto Kick/Ban Log: {'**Configured**' if self.sett.get('erlc', {}).get('kick_ban_log_channel', False) else '**Not Configured**'}\n"
                    f">  - Remote Command Logs: {'**Configured**' if self.sett.get('erlc', {}).get('command_log_channel', False) else '**Not Configured**'}\n\n"
                ),
                color=BLANK_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

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