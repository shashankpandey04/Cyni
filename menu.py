import discord
from discord.ext import commands
import logging
from utils.constants import BLANK_COLOR, GREEN_COLOR, RED_COLOR
from discord.ui import Button, View, Modal, TextInput
from bson import ObjectId

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
        prefix = None
        try:
            if self.sett.get('customization', {}).get('premium_prefix'):
                prefix = self.sett['customization']['premium_prefix']
            else:
                prefix = self.sett.get('customization', {}).get('prefix', "?")
        except KeyError:
            prefix = "?"

        prefix_options = ["?", "!", ">", ":"]
        options = []
        for opt in prefix_options:
            options.append(
            discord.SelectOption(
                label=opt,
                value=opt,
                default=prefix == opt
            )
            )
        if getattr(self.bot, "is_premium", False):
            premium_prefix = self.sett.get('customization', {}).get('premium_prefix', None)
            if premium_prefix and premium_prefix not in prefix_options:
                options.append(
                    discord.SelectOption(
                    label=premium_prefix,
                    value=premium_prefix,
                    default=prefix == premium_prefix
                    )
                )
        self.prefix_button = discord.ui.Select(
            placeholder="Select Prefix",
            options=options,
            row=0
        )
        self.prefix_button.callback = self.prefix_callback
        self.add_item(self.prefix_button)

        self.staff_role_select = discord.ui.RoleSelect(
            placeholder="Select Staff Roles",
            row=1,
            min_values=1,
            max_values=10,
            default_values=[discord.Object(id=role_id) for role_id in staff_roles if role_id is not None]
        )
        self.staff_role_select.callback = self.staff_roles_callback
        self.add_item(self.staff_role_select)

        self.management_role_select = discord.ui.RoleSelect(
            placeholder="Select Management Roles",
            row=2,
            min_values=1,
            max_values=10,
            default_values=[discord.Object(id=role_id) for role_id in management_roles if role_id is not None]
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
        try:
            if self.bot.is_premium:
                premium_server = await self.bot.premium.find_by_id(interaction.guild.id)
                if premium_server:
                    settings["customization"]["premium_prefix"] = self.prefix_button.values[0]
            else:
                settings["customization"]["prefix"] = self.prefix_button.values[0]
        except KeyError:
            settings = {"_id": interaction.guild.id, "customization": {"prefix": self.prefix_button.values[0]}}
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
        
        try:
            settings['basic_settings']['staff_roles'] = [role.id for role in self.staff_role_select.values]
        except KeyError:
            settings = {"_id": interaction.guild.id, "basic_settings": {"staff_roles": [role.id for role in self.staff_role_select.values]}}
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
        
        try:
            settings['basic_settings']['management_roles'] = [role.id for role in self.management_role_select.values]
        except KeyError:
            settings = {"_id": interaction.guild.id, "basic_settings": {"management_roles": [role.id for role in self.management_role_select.values]}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Management Roles Updated!", ephemeral=True)
class StaffInfraction(View):
    def __init__(self, bot,setting, user_id: int):
        super().__init__()

        self.bot = bot
        self.user_id = user_id
        self.sett = setting or {}

        try:
            enabled = self.sett.get("staff_management", {}).get("enabled", False)
        except KeyError:
            enabled = False

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
                    value="enable",
                    default=enabled == True or False
                ),
                discord.SelectOption(
                    label="Disable",
                    value="disable",
                    default=enabled == False or False
                )
            ]
        )
        self.enable_disable_select.callback = self.enable_disable_callback
        self.add_item(self.enable_disable_select)

        self.promotion_channel_select = discord.ui.ChannelSelect(
            placeholder="Staff Promotion Log Channel",
            row=1,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=promo_channel)] if promo_channel else [],
            channel_types=[discord.ChannelType.text]
        )

        self.promotion_channel_select.callback = self.promotion_channel
        self.add_item(self.promotion_channel_select)

        self.infraction_channel_select = discord.ui.ChannelSelect(
            placeholder="Staff Demotion Log Channel",
            row=2,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=demotion_channel)] if demotion_channel else [],
            channel_types=[discord.ChannelType.text]
        )
        self.infraction_channel_select.callback = self.infraction_channel
        self.add_item(self.infraction_channel_select)

        self.warning_channel_select = discord.ui.ChannelSelect(
            placeholder="Staff Warning Log Channel",
            row=3,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=warning_channel)] if warning_channel else [],
            channel_types=[discord.ChannelType.text]
        )
        self.warning_channel_select.callback = self.warning_channel
        self.add_item(self.warning_channel_select)

    async def enable_disable_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        if 'staff_management' not in settings:
            settings['staff_management'] = {'enabled': False}
        try:
            settings["staff_management"]["enabled"] = not settings["staff_management"].get("enabled",False)
        except KeyError:
            settings = {"_id": interaction.guild.id, "staff_management": {"enabled": True}}

        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
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

        try:
            enabled = self.sett.get("anti_ping_module", {}).get("enabled", False)
        except KeyError:
            enabled = False

        self.enable_disable_select = discord.ui.Select(
            placeholder="Enable / Disable Anti Ping",
            min_values=1,
            max_values=1,
            row=0,
            options=[
                discord.SelectOption(
                    label="Enable",
                    value="enable",
                    default=enabled == True or False
                ),
                discord.SelectOption(
                    label="Disable",
                    value="disable",
                    default=enabled == False or False
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
            default_values=[discord.Object(id=role_id) for role_id in affected_roles if role_id is not None]
        )
        self.affected_roles_button.callback = self.affected_roles_callback
        self.add_item(self.affected_roles_button)

        self.bypass_roles_button = discord.ui.RoleSelect(
            placeholder="Bypass Roles",
            row=2,
            min_values=1,
            max_values=25,
            default_values=[discord.Object(id=role_id) for role_id in bypass_roles if role_id is not None]
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
        await interaction.response.send_message(f"Your message quota is now {self.message_quota_input.value}", ephemeral=True)
        self.stop()

class ModerationModule(discord.ui.View):
    def __init__(self, bot, setting, user_id: int):
        super().__init__()
        self.bot = bot
        self.sett = setting
        self.user_id = user_id

        try:
            enabled = self.sett["moderation_module"]["enabled"]
        except KeyError:
            enabled = False

        self.enable_select = discord.ui.Select(
            placeholder="Enable/Disable Moderation Module",
            row=0,
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Enable",
                    value="enable",
                    default=enabled == True or False
                ),
                discord.SelectOption(
                    label="Disable",
                    value="disable",
                    default=enabled == False or False
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
                default_values=[discord.Object(id=mod_channel)] if mod_channel else [],
                channel_types=[discord.ChannelType.text]
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
            default_values=[discord.Object(id=appeal_channel)] if appeal_channel else [],
            channel_types=[discord.ChannelType.text]
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
            default_values=[discord.Object(id=audit_channel)] if audit_channel else [],
            channel_types=[discord.ChannelType.text]
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
            settings["moderation_module"]["audit_log"] = self.audit_channel_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "moderation_module": {"audit_log": self.audit_channel_select.values[0].id}}
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
                    value="enable",
                    default=enabled == True or False
                ),
                discord.SelectOption(
                    label="Disable",
                    value="disable",
                    default=enabled == False or False
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
            row=1,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=app_channel)] if app_channel else [],
            channel_types=[discord.ChannelType.text]
        )
        self.application_channel_select.callback = self.application_channel_callback
        self.add_item(self.application_channel_select)

        try:
            cyni_log_channel = self.sett["server_management"]["cyni_log_channel"]
        except KeyError:
            cyni_log_channel = 0
        self.cyni_log_channel_select = discord.ui.ChannelSelect(
            placeholder="Cyni Logging Channel",
            row=2,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=cyni_log_channel)] if cyni_log_channel else [],
            channel_types=[discord.ChannelType.text]
        )
        self.cyni_log_channel_select.callback = self.cyni_log_channel_callback
        self.add_item(self.cyni_log_channel_select)

        try:
            suggestion_channel = self.sett["server_management"]["suggestion_channel"]
        except KeyError:
            suggestion_channel = 0
        self.suggestion_channel_select = discord.ui.ChannelSelect(
            placeholder="Suggestion Channel",
            row=3,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=suggestion_channel)] if suggestion_channel else [],
            channel_types=[discord.ChannelType.text]
        )
        self.suggestion_channel_select.callback = self.suggestion_channel_callback
        self.add_item(self.suggestion_channel_select)

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

    async def suggestion_channel_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            settings["server_management"]["suggestion_channel"] = self.suggestion_channel_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "server_management": {"suggestion_channel": self.suggestion_channel_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Suggestion Channel Updated!",ephemeral=True)

class UpVote(discord.ui.Button):
    def __init__(self, row):
        super().__init__(label="Upvote", style=discord.ButtonStyle.success, row=row, emoji="👍")
        self.voters = set()

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        embeds = interaction.message.embeds[0]
        upvotes_field = embeds.fields[0]
        try:
            upvotes = int(upvotes_field.value) if upvotes_field.value and upvotes_field.value.isdigit() else 0
        except (ValueError, AttributeError):
            upvotes = 0

        if user.id in self.voters:
            self.voters.remove(user.id)
            upvotes -= 1
            await interaction.response.send_message(f"Your upvote has been removed.", ephemeral=True)
        else:
            self.voters.add(user.id)
            upvotes += 1
            await interaction.response.send_message(f"Your upvote has been added.", ephemeral=True)

        # Update the embed
        embeds.set_field_at(0, name="Upvotes", value=str(upvotes))
        await interaction.message.edit(embed=embeds, view=self.view)

class DownVote(discord.ui.Button):
    def __init__(self, row):
        super().__init__(label="Downvote", style=discord.ButtonStyle.danger, row=row, emoji="👎")
        self.voters = set()

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        embeds = interaction.message.embeds[0]
        downvotes_field = embeds.fields[1]
        try:
            downvotes = int(downvotes_field.value) if downvotes_field.value and downvotes_field.value.isdigit() else 0
        except (ValueError, AttributeError):
            downvotes = 0

        if user.id in self.voters:
            self.voters.remove(user.id)
            downvotes -= 1
            await interaction.response.send_message(f"Your downvote has been removed.", ephemeral=True)
        else:
            self.voters.add(user.id)
            downvotes += 1
            await interaction.response.send_message(f"Your downvote has been added.", ephemeral=True)

        # Update the embed
        embeds.set_field_at(1, name="Downvotes", value=str(downvotes))
        await interaction.message.edit(embed=embeds, view=self.view)

class ViewVotersButton(discord.ui.Button):
    def __init__(self, row, upvote_button, downvote_button):
        super().__init__(label="View Voters", style=discord.ButtonStyle.secondary, row=row,emoji="👥")
        self.upvote_button = upvote_button
        self.downvote_button = downvote_button

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Voters",
            color=BLANK_COLOR
        )
        embed.add_field(
            name="Upvotes",
            value="\n".join([f"<@{voter}>" for voter in self.upvote_button.voters]) if self.upvote_button.voters else "No voters yet."
        )
        embed.add_field(
            name="Downvotes",
            value="\n".join([f"<@{voter}>" for voter in self.downvote_button.voters]) if self.downvote_button.voters else "No voters yet."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class PartnershipModule(View):
    def __init__(self, bot, setting, user_id: int):
        super().__init__()
        self.bot = bot
        self.sett = setting
        self.user_id = user_id

        try:
            enabled = self.sett["partnership_module"]["enabled"]
        except KeyError:
            enabled = False

        self.enable_disable_select = discord.ui.Select(
            placeholder="Enable/Disable Partnership Module",
            row=0,
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Enable",
                    value="enable",
                    default=enabled == True or False
                ),
                discord.SelectOption(
                    label="Disable",
                    value="disable",
                    default=enabled == False or False
                )
            ]
        )
        self.enable_disable_select.callback = self.enable_disable_callback
        self.add_item(self.enable_disable_select)

        try:
            partnership_channel = self.sett["partnership_module"]["partnership_channel"]
        except KeyError:
            partnership_channel = 0
        self.partnership_channel_select = discord.ui.ChannelSelect(
            placeholder="Partnership Channel",
            row=1,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=partnership_channel)] if partnership_channel else [],
            channel_types=[discord.ChannelType.text]
        )
        self.partnership_channel_select.callback = self.partnership_channel_callback
        self.add_item(self.partnership_channel_select)

        try:
            partner_role = self.sett["partnership_module"]["partner_role"]
        except KeyError:
            partner_role = 0
        self.partner_role_select = discord.ui.RoleSelect(
            placeholder="Partner Role",
            row=2,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=partner_role)] if partner_role else []
        )
        self.partner_role_select.callback = self.partner_role_callback
        self.add_item(self.partner_role_select)

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
            settings["partnership_module"]["enabled"] = not settings["partnership_module"].get("enabled",False)
        except KeyError:
            settings = {"_id": interaction.guild.id, "partnership_module": {"enabled": True}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message(f"Partnership Module {'Enabled' if settings.get('partnership_module', {}).get('enabled', False) else 'Disabled'}",ephemeral=True)

    async def partnership_channel_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            settings["partnership_module"]["partnership_channel"] = self.partnership_channel_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "partnership_module": {"partnership_channel": self.partnership_channel_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Partnership Channel Updated!",ephemeral=True)

    async def partner_role_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            settings["partnership_module"]["partner_role"] = self.partner_role_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "partnership_module": {"partner_role": self.partner_role_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Partner Role Updated!",ephemeral=True)

class PremiumButton(View):
    def __init__(self):
        super().__init__()

        self.premium_button = discord.ui.Button(
            label="Cyni Premium",
            style=discord.ButtonStyle.secondary,
            emoji="💎",
            row=0,
            url="https://www.patreon.com/codingnerd04/membership"
        )
        self.add_item(self.premium_button)
        

class LOARequest(View):
    def __init__(self, bot, guild_id: int, user_id: int, schema_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.schema_id = schema_id

        self.accept_button = discord.ui.Button(
            label="Accept",
            style=discord.ButtonStyle.success,
            row=0,
            custom_id=f"loa_accept:{schema_id}"
        )

        self.deny_button = discord.ui.Button(
            label="Deny",
            style=discord.ButtonStyle.danger,
            row=0,
            custom_id=f"loa_deny:{schema_id}"
        )

        self.accept_button.callback = self.accept_callback
        self.deny_button.callback = self.deny_callback

        self.add_item(self.accept_button)
        self.add_item(self.deny_button)

    async def accept_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)

        document = await self.bot.loa.find_by_id(ObjectId(self.schema_id))
        if not isinstance(document, dict):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description="LOA Request not found.",
                    color=0xFF0000
                ),
                ephemeral=True
            )
        
        document["accepted"] = True
        
        await self.bot.loa.update_by_id(document)

        self.bot.dispatch("on_loa_accept", document)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="LOA Request Accepted",
                description="The LOA Request has been accepted.",
                color=0x00FF00
            ),
            ephemeral=True
        )

        embed = interaction.message.embeds[0]
        embed.set_footer(text=f"Accepted by {interaction.user}")
        embed.color = discord.Color.green()
        embed.title = "<:checked:1268849964063391788> LOA Request Accepted"
        
        user_id = document["user_id"]
        user = self.bot.get_user(user_id)

        if user is not None:
            try:
                await user.send(
                    embed=discord.Embed(
                        title=f"Activity Notice Accepted | {interaction.guild.name}",
                        description=f"Your {document['type']} request in **{interaction.guild.name}** was accepted!",
                        color=GREEN_COLOR,
                    )
                )
            except:
                print(f"Could not DM {user} about accepted LOA in {interaction.guild}")

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if settings is None:
            return
        
        loa_module = settings.get("leave_of_absence", {})
        role_ids = loa_module.get("loa_role", 0)
        
        if 0 == role_ids:
            return
        
        loa_role = interaction.guild.get_role(role_ids)
        if loa_role is None:
            return
        
        member = interaction.guild.get_member(user.id) or await interaction.guild.fetch_member(user.id)
        if member:
            await member.add_roles(loa_role, reason="LOA Accepted")
        await interaction.message.edit(embed=embed, view=None)

    async def deny_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)

        document = await self.bot.loa.find_by_id(ObjectId(self.schema_id))
        if not isinstance(document, dict):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description="LOA Request not found.",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        document["denied"] = True
        
        await self.bot.loa.update_by_id(document)

        self.bot.dispatch("on_loa_deny", document)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="LOA Request Denied",
                description="The LOA Request has been denied.",
                color=0xFF0000
            ),
            ephemeral=True
        )

        embed = interaction.message.embeds[0]
        embed.set_footer(text=f"Denied by {interaction.user}")
        embed.color = discord.Color.red()
        embed.title = "<:declined:1268849944455024671> LOA Request Denied"

        user_id = document["user_id"]
        user = self.bot.get_user(user_id)

        if user is not None:
            try:
                await user.send(
                    embed=discord.Embed(
                        title=f"Activity Notice Denied | {interaction.guild.name}",
                        description=f"Your {document['type']} request in **{interaction.guild.name}** was denied.",
                        color=RED_COLOR,
                    )
                )
            except:
                print(f"Could not DM {user} about denied LOA in {interaction.guild}")

        await interaction.message.edit(embed=embed, view=None)

class LOAConfig(discord.ui.View):
    def __init__(self, bot, setting, user_id: int):
        super().__init__()
        self.bot = bot
        self.sett = setting
        self.user_id = user_id

        try:
            enabled = self.sett["leave_of_absence"]["enabled"]
        except KeyError:
            enabled = False

        self.enable_disable_select = discord.ui.Select(
            placeholder="Enable/Disable LOA Module",
            row=0,
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Enable",
                    value="enable",
                    default=enabled == True or False
                ),
                discord.SelectOption(
                    label="Disable",
                    value="disable",
                    default=enabled == False or False
                )
            ]
        )
        self.enable_disable_select.callback = self.enable_disable_callback
        self.add_item(self.enable_disable_select)

        try:
            loa_channel = self.sett["leave_of_absence"]["loa_channel"]
        except KeyError:
            loa_channel = 0
        self.loa_channel_select = discord.ui.ChannelSelect(
            placeholder="LOA Channel",
            row=1,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=loa_channel)],
            channel_types=[discord.ChannelType.text]
        )
        self.loa_channel_select.callback = self.loa_channel_callback
        self.add_item(self.loa_channel_select)

        try:
            loa_role = self.sett["leave_of_absence"]["loa_role"]
        except KeyError:
            loa_role = 0
        self.loa_role_select = discord.ui.RoleSelect(
            placeholder="LOA Role",
            row=2,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=loa_role)]
        )
        self.loa_role_select.callback = self.loa_role_callback
        self.add_item(self.loa_role_select)

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
            settings["leave_of_absence"]["enabled"] = not settings["leave_of_absence"].get("enabled",False)
        except KeyError:
            settings = {"_id": interaction.guild.id, "leave_of_absence": {"enabled": True}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        await interaction.response.send_message(f"LOA Module {'Enabled' if settings.get('leave_of_absence', {}).get('enabled', False)

            else 'Disabled'}",ephemeral=True)
        
    async def loa_channel_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            settings["leave_of_absence"]["loa_channel"] = self.loa_channel_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "leave_of_absence": {"loa_channel": self.loa_channel_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("LOA Channel Updated!",ephemeral=True)

    async def loa_role_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            settings["leave_of_absence"]["loa_role"] = self.loa_role_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "leave_of_absence": {"loa_role": self.loa_role_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("LOA Role Updated!",ephemeral=True)
        