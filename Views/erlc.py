import discord
from discord.ext import commands
from utils.constants import BLANK_COLOR, GREEN_COLOR, RED_COLOR
from discord.ui import Button, View, Modal, TextInput

class CustomModal(discord.ui.Modal):
    def __init__(self, title: str, inputs: list[tuple[str, discord.ui.TextInput]]):
        super().__init__(title=title, timeout=300)  # 5 min timeout
        self.values = {}  # store results

        for custom_id, text_input in inputs:
            # assign an ID for retrieval
            text_input.custom_id = custom_id
            self.add_item(text_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Save all inputs into self.values
        for child in self.children:
            if isinstance(child, discord.ui.TextInput):
                self.values[child.custom_id] = child.value
        await interaction.response.defer()  # acknowledge modal submit (no message sent)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(
            f"An error occurred: {error}", ephemeral=True
        )

class LoggingChannels(View):
    def __init__(self, bot, ctx, sett):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.sett = sett
        try:
            kill_logs_channel = self.sett.get('erlc', {}).get('kill_logs_channel', None)
            join_logs_channel = self.sett.get('erlc', {}).get('join_logs_channel', None)
            discord_check_log_channel = self.sett.get('erlc', {}).get('discord_check_log_channel', None)
        except KeyError:
            kill_logs_channel = None
            join_logs_channel = None
            discord_check_log_channel = None

        self.kill_logs_channel = discord.ui.ChannelSelect(
            placeholder="Kill Logs Channel",
            row=0,
            channel_types=[discord.ChannelType.text],
            default_values=[discord.Object(id=kill_logs_channel)] if kill_logs_channel else []
        )

        self.join_logs_channel = discord.ui.ChannelSelect(
            placeholder="Join Logs Channel",
            row=1,
            channel_types=[discord.ChannelType.text],
            default_values=[discord.Object(id=join_logs_channel)] if join_logs_channel else []
        )

        self.discord_check_log_button = discord.ui.Button(
            label="Auto Discord Checks",
            style=discord.ButtonStyle.secondary,
            row=2
        )

        self.kick_ban_log_channel_button = discord.ui.Button(
            label="Kick/Ban Auto Logging",
            style=discord.ButtonStyle.secondary,
            row=2
        )

        self.command_log_channel_button = discord.ui.Button(
            label="Command Auto Logging",
            style=discord.ButtonStyle.secondary,
            row=2
        )

        self.add_item(self.kill_logs_channel)
        self.add_item(self.join_logs_channel)
        self.add_item(self.discord_check_log_button)
        self.add_item(self.kick_ban_log_channel_button)
        self.add_item(self.command_log_channel_button)
        self.kill_logs_channel.callback = self.kill_logs_channel_callback
        self.join_logs_channel.callback = self.join_logs_channel_callback
        self.discord_check_log_button.callback = self.discord_check_log_channel_callback
        self.kick_ban_log_channel_button.callback = self.kick_ban_log_channel_callback
        self.command_log_channel_button.callback = self.command_log_channel_callback

    async def kill_logs_channel_callback(self, interaction: discord.Interaction):
        channel_id = self.kill_logs_channel.values[0].id if self.kill_logs_channel.values else None
        
        # Update local settings
        self.sett['erlc']['kill_logs_channel'] = channel_id
        
        # Save to database
        await self.bot.settings.update_one(
            {"_id": interaction.guild.id},
            {"$set": self.sett},
            upsert=True
        )

        
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Kill Logs Channel Updated",
                description="The ERLC kill logs channel has been updated successfully.",
                color=GREEN_COLOR
            ),
            ephemeral=True
        )

        channel = self.bot.get_channel(channel_id)
        embed = discord.Embed(
            title="Kill Logs Channel",
            description=f"This channel will now log all ERLC kill actions.",
            color=GREEN_COLOR
        ).set_author(
            name="Cyni Bot",
            url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        await channel.send(embed=embed)

    async def join_logs_channel_callback(self, interaction: discord.Interaction):
        channel_id = self.join_logs_channel.values[0].id if self.join_logs_channel.values else None
        
        # Update local settings
        self.sett['erlc']['join_logs_channel'] = channel_id
        
        # Save to database
        await self.bot.settings.update_one(
            {"_id": interaction.guild.id},
            {"$set": self.sett},
            upsert=True
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Join Logs Channel Updated",
                description="The ERLC join logs channel has been updated successfully.",
                color=GREEN_COLOR
            ),
            ephemeral=True
        )

        channel = self.bot.get_channel(channel_id)
        embed = discord.Embed(
            title="Join Logs Channel",
            description=f"This channel will now log all ERLC join actions.",
            color=GREEN_COLOR
        ).set_author(
            name="Cyni Bot",
            url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        await channel.send(embed=embed)

    async def discord_check_log_channel_callback(self, interaction: discord.Interaction):
        setting = await self.bot.settings.find_by_id(interaction.guild.id)
        discord_checks = setting.get("erlc", {}).get("discord_checks", {})
        embed = discord.Embed(
            title="Automated Discord Checks",
            description="This module allows for automated checks on Discord accounts of players in your server. If a player fails the checks, they will be alerted in-game and can be kicked if configured.",
            color=BLANK_COLOR
        ).set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        ).add_field(
            name="Enabled/Disabled Discord Checks",
            value=f"> **Current Status:** {'Enabled' if discord_checks.get('enabled', False) else 'Disabled'}",
            inline=True
        ).add_field(
            name="Alert Channel",
            value=f"> CYNI will send alerts to this channel if a user fails the Discord checks.\n> **Current Channel:** <#{discord_checks.get('channel_id', 'None')}>",
            inline=True
        ).add_field(
            name="Alert Message",
            value=f"> **Current Message:** {discord_checks.get('message', 'Please join the Private Server Communication channel.')}",
            inline=True
        ).add_field(
            name="Kick After",
            value=f"> After how many in-game alert users will be kicked?\n> **Current:** {discord_checks.get('kick_after', 'None')}",
            inline=True
        )
        view = ERLCDiscordChecksConfiguration(self.bot, interaction.user.id, self.sett)
        await interaction.response.send_message(view=view, ephemeral=True, embed=embed)

    async def kick_ban_log_channel_callback(self, interaction: discord.Interaction):
        setting = await self.bot.settings.find_by_id(interaction.guild.id)
        kick_ban_log_channel = setting.get("erlc", {}).get("kick_ban_log_channel", {})
        embed = discord.Embed(
            title="ERLC Command Log Channel",
            description="This channel will log all ERLC command usage.",
            color=BLANK_COLOR
        ).set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        ).add_field(
            name="Current Channel",
            value=f"> **Current Channel:** <#{kick_ban_log_channel}>" if kick_ban_log_channel else "> **Current Channel:** None",
            inline=True
        )
        view = KickBanCommandLogChannel(self.bot, interaction.user.id, self.sett)
        await interaction.response.send_message(view=view, ephemeral=True, embed=embed)

    async def command_log_channel_callback(self, interaction: discord.Interaction):
        setting = await self.bot.settings.find_by_id(interaction.guild.id)
        erlc_command_log_channel = setting.get("erlc", {}).get("command_log_channel", {})
        embed = discord.Embed(
            title="ERLC Command Log Channel",
            description="This channel will log all ERLC command usage.",
            color=BLANK_COLOR
        ).set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else "",
        ).add_field(
            name="Current Channel",
            value=f"> **Current Channel:** <#{erlc_command_log_channel}>" if erlc_command_log_channel else "> **Current Channel:** None",
            inline=True
        )
        view = ERLCCommandLogChannel(self.bot, interaction.user.id, self.sett)
        await interaction.response.send_message(view=view, ephemeral=True, embed=embed)

class ERLCCommandLogChannel(discord.ui.View):
    def __init__(self, bot: commands.Bot, user_id: int, sett: dict):
        super().__init__(timeout=900.0)
        self.bot = bot
        self.sett = sett
        self.user_id = user_id

        self.command_log_channel = sett.get("erlc", {}).get("command_log_channel", 0)

        self.channel_select = discord.ui.ChannelSelect(
            placeholder="Select Command Log Channel",
            channel_types=[discord.ChannelType.text],
            default_values=[discord.Object(id=self.command_log_channel)] if self.command_log_channel else None,
            row=0,
            max_values=1,
        )
        self.channel_select.callback = self.channel_select_callback
        self.add_item(self.channel_select)

    async def channel_select_callback(self, interaction: discord.Interaction):
        """Callback for the channel select menu."""
        self.command_log_channel = self.channel_select.values[0].id
        await self.bot.settings.update_one(
            {"_id": interaction.guild.id},
            {"$set": {"erlc.command_log_channel": self.command_log_channel}}
        )
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Command Log Channel Updated",
                description=f"Command log channel has been updated to <#{self.command_log_channel}>.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

class KickBanCommandLogChannel(discord.ui.View):
    def __init__(self, bot: commands.Bot, user_id: int, sett: dict):
        super().__init__(timeout=900.0)
        self.bot = bot
        self.sett = sett
        self.user_id = user_id

        self.command_log_channel = sett.get("erlc", {}).get("kick_ban_log_channel", 0)

        self.channel_select = discord.ui.ChannelSelect(
            placeholder="Select Kick/Ban Log Channel",
            channel_types=[discord.ChannelType.text],
            default_values=[discord.Object(id=self.command_log_channel)] if self.command_log_channel else None,
            row=0,
            max_values=1,
        )
        self.channel_select.callback = self.channel_select_callback
        self.add_item(self.channel_select)

    async def channel_select_callback(self, interaction: discord.Interaction):
        """Callback for the channel select menu."""
        self.command_log_channel = self.channel_select.values[0].id
        await self.bot.settings.update_one(
            {"_id": interaction.guild.id},
            {"$set": {"erlc.kick_ban_log_channel": self.command_log_channel}}
        )
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Kick/Ban Log Channel Updated",
                description=f"Kick/Ban log channel has been updated to <#{self.command_log_channel}>.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )


class ERLCDiscordChecksConfiguration(discord.ui.View):
    def __init__(self, bot: commands.Bot, user_id: int, sett: dict):
        super().__init__(timeout=900.0)
        self.bot = bot
        self.sett = sett
        self.user_id = user_id
        
        self.discord_checks = sett.get("erlc", {}).get("discord_checks", {})
        enabled = self.discord_checks.get("enabled", False)
        channel_id = self.discord_checks.get("channel_id")
        kick_after = self.discord_checks.get("kick_after", 4)
        
        self._setup_components(enabled, channel_id, kick_after)
    
    def _setup_components(self, enabled: bool, channel_id: int, kick_after: int):
        self.enable_button = discord.ui.Select(
            placeholder="Enable/Disable Discord Checks",
            options=[
                discord.SelectOption(label="Enabled", value="enabled", default=enabled),
                discord.SelectOption(label="Disabled", value="disabled", default=not enabled),
            ],
            row=0,
            max_values=1,
        )
        self.enable_button.callback = self.enable_button_callback
        self.add_item(self.enable_button)

        default_values = [discord.Object(id=channel_id)] if channel_id else None
        self.alert_channel_select = discord.ui.ChannelSelect(
            placeholder="Select Alert Channel",
            channel_types=[discord.ChannelType.text],
            default_values=default_values,
            row=1,
            max_values=1,
        )
        self.alert_channel_select.callback = self.alert_channel_select_callback
        self.add_item(self.alert_channel_select)

        self.kick_after = discord.ui.Select(
            placeholder="Select Kick After (warnings)",
            options=[
                discord.SelectOption(
                    label=f"{i} warning{'s' if i > 1 else ''}", 
                    value=str(i),
                    default=(i == kick_after)
                ) for i in range(1, 11)
            ],
            row=2,
        )
        self.kick_after.callback = self.kick_after_callback
        self.add_item(self.kick_after)

        self.alert_message = discord.ui.Button(
            label="Set Alert Message", 
            style=discord.ButtonStyle.secondary,
            row=3
        )
        self.alert_message.callback = self.alert_message_callback
        self.add_item(self.alert_message)

    async def _check_permissions(self, interaction: discord.Interaction) -> bool:
        """Check if user has permission to interact with this view"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not permitted to interact with these buttons.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return False
        return True
    
    async def _ensure_settings_structure(self, sett: dict) -> None:
        """Ensure the nested dictionary structure exists"""
        if "erlc" not in sett:
            sett["erlc"] = {}
        if "discord_checks" not in sett["erlc"]:
            sett["erlc"]["discord_checks"] = {"enabled": False}
    
    async def _update_settings_and_log(self, interaction: discord.Interaction, sett: dict, message: str) -> None:
        """Update settings and log the change"""
        await self.bot.settings.update_by_id(sett)
    
    async def _update_embed_field(self, interaction: discord.Interaction, field_index: int, name: str, value: str) -> None:
        """Update a specific field in the embed"""
        embed = interaction.message.embeds[0]
        embed.set_field_at(field_index, name=name, value=value, inline=True)
        await interaction.edit_original_response(embed=embed, view=self)

    async def enable_button_callback(self, interaction: discord.Interaction):
        if not await self._check_permissions(interaction):
            return
        
        await interaction.response.defer()
        
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        await self._ensure_settings_structure(sett)
        
        enabled = self.enable_button.values[0] == "enabled"
        sett["erlc"]["discord_checks"]["enabled"] = enabled

        if enabled and "channel_id" not in sett["erlc"]["discord_checks"]:
            sett["erlc"]["discord_checks"]["channel_id"] = None
        
        await self._update_settings_and_log(
            interaction, sett, 
            f"Discord Checks have been {'enabled' if enabled else 'disabled'}."
        )

        for option in self.enable_button.options:
            option.default = False
        
        await self._update_embed_field(
            interaction, 0, 
            "Enabled/Disabled Discord Checks", 
            f"> **Current Status:** {'Enabled' if enabled else 'Disabled'}"
        )

    async def alert_channel_select_callback(self, interaction: discord.Interaction):
        if not await self._check_permissions(interaction):
            return
        
        await interaction.response.defer()
        
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        await self._ensure_settings_structure(sett)
        
        channel_id = self.alert_channel_select.values[0].id if self.alert_channel_select.values else None
        sett["erlc"]["discord_checks"]["channel_id"] = channel_id
        
        await self._update_settings_and_log(
            interaction, sett,
            f"Discord Checks Channel has been set to <#{channel_id}>."
        )
        
        await self._update_embed_field(
            interaction, 1,
            "Discord Check Channel",
            f"> **Current Channel:** <#{channel_id}>"
        )

    async def kick_after_callback(self, interaction: discord.Interaction):
        if not await self._check_permissions(interaction):
            return
        
        await interaction.response.defer()
        
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        await self._ensure_settings_structure(sett)
        
        kick_after = int(self.kick_after.values[0]) if self.kick_after.values else 4
        sett["erlc"]["discord_checks"]["kick_after"] = kick_after
        
        await self._update_settings_and_log(
            interaction, sett,
            f"Discord Checks Kick After has been set to {kick_after} warnings."
        )
        
        await self._update_embed_field(
            interaction, 2,
            "Kick After",
            f"> **Current Duration:** {kick_after} warning{'s' if kick_after > 1 else ''}"
        )

    async def alert_message_callback(self, interaction: discord.Interaction):
        if not await self._check_permissions(interaction):
            return

        modal = CustomModal(
            "Alert Message Configuration",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Alert Message",
                        placeholder="Enter the message to send when Discord checks fail.",
                        required=True,
                        max_length=500
                    )
                )
            ],
        )
        
        await interaction.response.send_modal(modal)
        
        if await modal.wait():
            return

        alert_message = modal.value
        if not alert_message:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Alert Message Provided",
                    description="You must provide an alert message.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        await self._ensure_settings_structure(sett)
        sett["erlc"]["discord_checks"]["message"] = alert_message
        
        await self._update_settings_and_log(
            interaction, sett,
            f"Discord Checks Alert Message has been set to: {alert_message}"
        )

        await interaction.followup.send(
            embed=discord.Embed(
                title="Alert Message Set",
                description=f"Your alert message has been set to: {alert_message}",
                color=BLANK_COLOR
            ), ephemeral=True
        )
        
        # Update the embed
        embed = interaction.message.embeds[0]
        embed.set_field_at(3, name="Alert Message", value=f"> **Current Message:** {alert_message}", inline=True)
        await interaction.edit_original_response(embed=embed, view=self)