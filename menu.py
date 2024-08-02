import discord
from discord.ext import commands
import logging
from utils.constants import BLANK_COLOR
from discord.ui import Button, View, Modal, TextInput

class BasicConfig(discord.ui.View):
    def __init__(self, bot, sett, user_id: int):
        super().__init__()
        self.bot = bot
        self.sett = sett or {}
        self.user_id = user_id
        
        try:
            staff_roles = self.sett['basic_settings']['staff_roles'] if 'staff_roles' in self.sett['basic_settings'] else []
            management_roles = self.sett['basic_settings']['management_roles'] if 'management_roles' in self.sett['basic_settings'] else []
        except KeyError:
            staff_roles = []
            management_roles = []
        try:
            prefix = self.sett['customization']['prefix']
        except KeyError:
            prefix = "?"

        self.prefix_button = discord.ui.Select(
            placeholder="Select Prefix",
            options=[
                discord.SelectOption(
                    label="?",
                    value="?"
                ),
                discord.SelectOption(
                    label="!",
                    value="!"
                ),
                discord.SelectOption(
                    label=">",
                    value=">"
                ),
                discord.SelectOption(
                    label=":",
                    value=":"
                )
            ],
            row=0
        )
        self.prefix_button.callback = self.prefix_callback
        self.add_item(self.prefix_button)

        self.staff_role_select = discord.ui.RoleSelect(
            placeholder="Select Staff Roles",
            row=1,
            min_values=1,
            max_values=10,
            default_values=[discord.Object(id=role_id) for role_id in staff_roles]
        )
        self.staff_role_select.callback = self.staff_roles_callback
        self.add_item(self.staff_role_select)

        self.management_role_select = discord.ui.RoleSelect(
            placeholder="Select Management Roles",
            row=2,
            min_values=1,
            max_values=10,
            default_values=[discord.Object(id=role_id) for role_id in management_roles]
        )
        self.management_role_select.callback = self.management_roles_callback
        self.add_item(self.management_role_select)

    async def prefix_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not allowed to use this menu.",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "customization": {}}
        
        settings.setdefault("customization", {})["prefix"] = self.prefix_button.values[0]

        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Prefix Updated!", ephemeral=True)

    async def staff_roles_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not allowed to use this menu.",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "basic_settings": {}}
        
        settings.setdefault("basic_settings", {})["staff_roles"] = [
            role.id for role in self.staff_role_select.values
        ]

        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Staff Roles Updated!", ephemeral=True)

    async def management_roles_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You are not allowed to use this menu.",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "basic_settings": {}}
        
        settings.setdefault("basic_settings", {})["management_roles"] = [
            role.id for role in self.management_role_select.values
        ]

        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Management Roles Updated!", ephemeral=True)
class StaffInfraction(View):
    def __init__(self, bot,setting, user_id: int):
        super().__init__()

        self.bot = bot
        self.user_id = user_id
        self.sett = setting or {}

        try:
            promo_channel = self.sett.get("staff_management", {}).get("promotion_channel", 0)
        except KeyError:
            promo_channel = 0
        try:
            demotion_channel = self.sett.get("staff_management", {}).get("demotion_channel", 0)
        except KeyError:
            demotion_channel = 0
        try:
            warning_channel = self.sett.get("staff_management", {}).get("warning_channel", 0)
        except KeyError:
            warning_channel = 0

        self.enable_disable_select = discord.ui.Select(
            placeholder="Enable/Disable Staff Infraction Module",
            row=0,
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Enable",
                    value="enable"
                ),
                discord.SelectOption(
                    label="Disable",
                    value="disable"
                )
            ]
        )
        self.enable_disable_select.callback = self.enable_disable_callback
        self.add_item(self.enable_disable_select)

        self.promotion_channel_select = discord.ui.ChannelSelect(
            placeholder="Staff Promotion Log Channel",
            row=1,
            min_values=0,
            max_values=1,
            default_values=[discord.Object(id=promo_channel)]
        )

        self.promotion_channel_select.callback = self.promotion_channel
        self.add_item(self.promotion_channel_select)

        self.infraction_channel_select = discord.ui.ChannelSelect(
            placeholder="Staff Demotion Log Channel",
            row=2,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=demotion_channel)]
        )
        self.infraction_channel_select.callback = self.infraction_channel
        self.add_item(self.infraction_channel_select)

        self.warning_channel_select = discord.ui.ChannelSelect(
            placeholder="Staff Warning Log Channel",
            row=3,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=warning_channel)]
        )
        self.warning_channel_select.callback = self.warning_channel
        self.add_item(self.warning_channel_select)

    async def enable_disable_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            staff_infraction_module = settings['staff_management']
        except KeyError:
            settings = {
                '_id': interaction.guild.id,
                'staff_management': {'enabled': False}
            }
        try:
            settings["staff_management"]["enabled"] = not settings["staff_management"].get("enabled",False)
        except KeyError:
            settings = {"_id": interaction.guild.id, "staff_management": {"enabled": True}}

        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="Enable/Disable Staff Infraction Module",
            value=f"{'Enabled' if settings.get('staff_management', {}).get('enabled', False) else 'Disabled'}"
        )
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"Staff Infraction Module {'Enabled' if settings.get('staff_management', {}).get('enabled', False) else 'Disabled'}",ephemeral=True)

    async def promotion_channel(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "staff_management": {}}
        try:
            settings["staff_management"]["promotion_channel"] = self.promotion_channel_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "staff_management": {"promotion_channel": self.promotion_channel_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Promotion Channel Updated!",ephemeral=True)

    async def infraction_channel(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "staff_management": {}}
        try:
            settings["staff_management"]["demotion_channel"] = self.infraction_channel_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "staff_management": {"demotion_channel": self.infraction_channel_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Infraction Channel Updated!",ephemeral=True)

    async def warning_channel(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "staff_management": {}}
        try:
            settings["staff_management"]["warning_channel"] = self.warning_channel_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "staff_management": {"warning_channel": self.warning_channel_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Warning Channel Updated!",ephemeral=True)

class AntiPingView(View):
    def __init__(self,bot,sett, user_id:int):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.sett = sett or {}

        self.enable_disable_select = discord.ui.Select(
            placeholder="Enable / Disable Anti Ping",
            min_values=1,
            max_values=1,
            row=0,
            options=[
                discord.SelectOption(
                    label="Enable",
                    value="enable"
                ),
                discord.SelectOption(
                    label="Disable",
                    value="disable"
                )
            ]
        )
        self.enable_disable_select.callback = self.enable_disable_callback
        self.add_item(self.enable_disable_select)

        try:
            affected_roles = self.sett.get("anti_ping_module", {}).get("affected_roles", [])
            bypass_roles = self.sett.get("anti_ping_module", {}).get("exempt_roles", [])
        except KeyError:
            affected_roles = []
            bypass_roles = []

        self.affected_roles_button = discord.ui.RoleSelect(
            placeholder="Affected Roles",
            row=1,
            min_values=1,
            max_values=25,
            default_values=[discord.Object(id=role_id) for role_id in affected_roles]
        )
        self.affected_roles_button.callback = self.affected_roles_callback
        self.add_item(self.affected_roles_button)

        self.bypass_roles_button = discord.ui.RoleSelect(
            placeholder="Bypass Roles",
            row=2,
            min_values=1,
            max_values=25,
            default_values=[discord.Object(id=role_id) for role_id in bypass_roles]
        )
        self.bypass_roles_button.callback = self.bypass_roles_callback
        self.add_item(self.bypass_roles_button)

    async def enable_disable_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "anti_ping_module": {}}
        try:
            settings["anti_ping_module"]["enabled"] = not settings["anti_ping_module"].get("enabled",False)
        except KeyError:
            settings = {"_id": interaction.guild.id, "anti_ping_module": {"enabled": True}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="Enable/Disable Anti-Ping Module",
            value=f"{'Enabled' if settings.get('anti_ping_module', {}).get('enabled', False) else 'Disabled'}"
        )
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(
            f"Anti Ping Module {'Enabled' if settings.get('anti_ping_module', {}).get('enabled', False) else 'Disabled'}",
            ephemeral=True
        )

    async def affected_roles_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
            
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "anti_ping_module": {}}
        try:
            settings["anti_ping_module"]["affected_roles"] = [role.id for role in self.affected_roles_button.values]
        except KeyError:
            settings = {"_id": interaction.guild.id, "anti_ping_module": {"affected_roles": [role.id for role in self.affected_roles_button.values]}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Affected Roles Updated!",ephemeral=True)

    async def bypass_roles_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "anti_ping_module": {}}
        try:
            settings["anti_ping_module"]["exempt_roles"] = [role.id for role in self.bypass_roles_button.values]
        except KeyError:
            settings = {"_id": interaction.guild.id, "anti_ping_module": {"exempt_roles": [role.id for role in self.bypass_roles_button.values]}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Bypass Roles Updated!",ephemeral=True)

class MessageQuotaModal(Modal):
    def __init__(self):
        super().__init__(title="Change Message Quota", timeout=60)
        
        self.message_quota_input = TextInput(
            placeholder="Enter your message quota",
            min_length=1,
            max_length=5,
            label="Message Quota"
        )
        self.add_item(self.message_quota_input)

    async def on_submit(self, interaction: discord.Interaction):
        settings = await interaction.client.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        if "basic_settings" not in settings:
            settings["basic_settings"] = {}
        try:
            settings["basic_settings"]["message_quota"] = self.message_quota_input.value
        except KeyError:
            settings = {"_id": interaction.guild.id, "basic_settings": {"message_quota": self.message_quota_input.value}}
        await interaction.client.settings.update({"_id": interaction.guild.id}, settings)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="Message Quota",
            value=f"> Set the message quota for your server.\nCurrent Message Quota: {self.message_quota_input.value}"
        )

        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"Your message quota is now {self.message_quota_input.value}", ephemeral=True)
        self.stop()

class ModerationModule(discord.ui.View):
    def __init__(self, bot, setting, user_id: int):
        super().__init__()
        self.bot = bot
        self.sett = setting
        self.user_id = user_id

        self.enable_select = discord.ui.Select(
            placeholder="Enable/Disable Moderation Module",
            row=0,
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Enable",
                    value="enable"
                ),
                discord.SelectOption(
                    label="Disable",
                    value="disable"
                )
            ],
        )
        self.enable_select.callback = self.enable_select_callback
        
        try:
            mod_channel = self.sett["moderation_module"]["mod_log_channel"]
        except KeyError:
            mod_channel = 0
        self.moderation_log_channel_select = discord.ui.ChannelSelect(
                placeholder="Moderation Log Channel",
                row=1,
                min_values=1,
                max_values=1,
                default_values=[discord.Object(id=mod_channel)]
        )
        self.moderation_log_channel_select.callback = self.moderation_log_channel_callback

        try:
            appeal_channel = self.sett["moderation_module"]["ban_appeal_channel"]
        except KeyError:
            appeal_channel = 0
        self.ban_appeal_channel = discord.ui.ChannelSelect(
            placeholder="Ban Appeal Log Channel",
            row=2,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=appeal_channel)]
        )
        self.ban_appeal_channel.callback = self.ban_appeal_channel_callback

        try:
            audit_channel = self.sett["moderation_module"]["audit_channel"]
        except:
            audit_channel = 0

        self.audit_channel_select = discord.ui.ChannelSelect(
            placeholder="Audit Log Channel",
            min_values=0,
            max_values=1,
            row=3,
            default_values=[discord.Object(id=audit_channel)]
        )
        self.audit_channel_select.callback = self.audit_channel_select_callback
        self.children.append(self.audit_channel_select)
        
        self.add_item(self.enable_select)
        self.add_item(self.moderation_log_channel_select)
        self.add_item(self.ban_appeal_channel)
        self.add_item(self.audit_channel_select)

    async def enable_select_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            settings["moderation_module"]["enabled"] = True if self.enable_select.values[0] == "enable" else False
        except KeyError:
            settings = {"_id": interaction.guild.id, "moderation_module": {"enabled": True if self.enable_select.values[0] == "enable" else False}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="Enable/Disable Moderation Module",
            value=f"{'Enabled' if settings.get('moderation_module', {}).get('enabled', False) else 'Disabled'}"
        )
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"Moderation Module {'Enabled' if settings.get('moderation_module', {}).get('enabled', False) else 'Disabled'}",ephemeral=True)

    async def moderation_log_channel_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            settings["moderation_module"]["mod_log_channel"] = self.moderation_log_channel_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "moderation_module": {"mod_log_channel": self.moderation_log_channel_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Moderation Log Channel Updated!",ephemeral=True)

    async def ban_appeal_channel_callback(self,interaction:discord.Interaction):
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "moderation_module": {}}
        try:
            settings["moderation_module"]["ban_appeal_channel"] = self.ban_appeal_channel.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "moderation_module": {"ban_appeal_channel": self.ban_appeal_channel.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Ban Appeal Log Channel Updated!",ephemeral=True)

    async def audit_channel_select_callback(self,interaction:discord.Interaction):
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "moderation_module": {}}
        try:
            settings["moderation_module"]["audit_log"] = self.ban_appeal_channel.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "moderation_module": {"audit_log": self.ban_appeal_channel.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Audit Log Channel Updated!",ephemeral=True)
    
class ServerManagement(discord.ui.View):
    def __init__(self, bot, setting, user_id: int):
        super().__init__()
        self.bot = bot
        self.sett = setting
        self.user_id = user_id

        try:
            enabled = self.sett["server_management"]["enabled"]
        except KeyError:
            enabled = False

        self.enable_disable_select = discord.ui.Select(
            placeholder="Enable/Disable Server Management Module",
            row=0,
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Enable",
                    value="enable"
                ),
                discord.SelectOption(
                    label="Disable",
                    value="disable"
                )
            ]
        )
        self.enable_disable_select.callback = self.enable_disable_callback
        self.add_item(self.enable_disable_select)

        try:
            app_channel = self.sett["server_management"]["application_channel"]
        except KeyError:
            app_channel = 0
        self.application_channel_select = discord.ui.ChannelSelect(
            placeholder="Application Results Channel",
            row=0,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=app_channel)]
        )
        self.application_channel_select.callback = self.application_channel_callback
        self.add_item(self.application_channel_select)

        try:
            cyni_log_channel = self.sett["server_management"]["cyni_log_channel"]
        except KeyError:
            cyni_log_channel = 0
        self.cyni_log_channel_select = discord.ui.ChannelSelect(
            placeholder="Cyni Logging Channel",
            row=1,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=cyni_log_channel)]
        )
        self.cyni_log_channel_select.callback = self.cyni_log_channel_callback
        self.add_item(self.cyni_log_channel_select)

    async def enable_disable_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            settings["server_management"]["enabled"] = not settings["server_management"].get("enabled",False)
        except KeyError:
            settings = {"_id": interaction.guild.id, "server_management": {"enabled": True}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="Enable/Disable Server Management Module",
            value=f"{'Enabled' if settings.get('server_management', {}).get('enabled', False) else 'Disabled'}"
        )
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"Server Management Module {'Enabled' if settings.get('server_management', {}).get('enabled', False) else 'Disabled'}",ephemeral=True)

    async def application_channel_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            settings["server_management"]["application_channel"] = self.application_channel_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "server_management": {"application_channel": self.application_channel_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Application Channel Updated!",ephemeral=True)

    async def cyni_log_channel_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            settings["server_management"]["cyni_log_channel"] = self.cyni_log_channel_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "server_management": {"cyni_log_channel": self.cyni_log_channel_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Cyni Log Channel Updated!",ephemeral=True)