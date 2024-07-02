import discord
from discord.ext import commands


from discord.ui import Button, View, Modal, TextInput

from utils.utils import main_config_embed

class BasicConfiguration(View):
    def __init__(self, bot: commands.Bot,user_id:int):
        super().__init__()

        self.bot = bot
        self.user_id = user_id

        self.staff_role_select = discord.ui.RoleSelect(
            placeholder="Staff Roles",
            row=0,
            min_values=1,
            max_values=10,
        )
        self.staff_role_select.callback = self.staff_roles
        self.add_item(self.staff_role_select)

        self.management_role_select = discord.ui.RoleSelect(
            placeholder="Management Roles",
            row=1,
            min_values=1,
            max_values=10,
        )
        self.management_role_select.callback = self.management_roles
        self.add_item(self.management_role_select)

        self.main_page = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Main Page",
            row=4
        )
        self.main_page.callback = self.main_page_callback
        self.add_item(self.main_page)

    async def main_page_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        await interaction.message.edit(embed=main_config_embed,view=Configuration(self.bot, interaction.user.id))
        await interaction.response.send_message("Main Page",ephemeral=True)

    async def staff_roles(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "basic_settings": {}}
        
        settings["basic_settings"]["staff_roles"] = [role.id for role in self.staff_role_select.values]
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="Staff Roles",
            value=f"""
            > These roles grant permission to use Cyni moderation commands.\n
            Current Roles: {"<@&" + ">, <@&".join([str(role) for role in settings.get("basic_settings", {}).get("staff_roles", [])]) + ">"}
            """,
            inline=False
        )
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("Staff Roles Updated!",ephemeral=True)

    async def management_roles(self, interaction: discord.Interaction):
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "basic_settings": {}}
        
        settings["basic_settings"]["management_roles"] = [role.id for role in self.management_role_select.values]
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            1,
            name="Management Roles",
            value=f"""
            > Users with these roles can utilize Cyni management commands, including Application Result commands, Staff Promo/Demo command, and setting the Moderation Log channel
            Current Roles: {"<@&" + ">, <@&".join([str(role) for role in settings.get("basic_settings", {}).get("management_roles", [])]) + ">"}
            """,
            inline=False
        )
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("Management Roles Updated!",ephemeral=True)

class StaffInfraction(View):
    def __init__(self, bot: commands.Bot, user_id: int,promo_channel:int,demotion_channel:int,enalbed:bool):
        super().__init__()

        self.bot = bot
        self.user_id = user_id
        self.promo_channel = promo_channel
        self.demotion_channel = demotion_channel
        self.enalbed = enalbed

        self.enable_disable_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Enable/Disable Staff Infraction Module",
            row=0
        )
        self.enable_disable_button.callback = self.enable_disable_callback
        self.add_item(self.enable_disable_button)

        self.promotion_channel_select = discord.ui.ChannelSelect(
            placeholder="Promotion Channel",
            row=1,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=self.promo_channel)]
        )

        self.promotion_channel_select.callback = self.promotion_channel
        self.add_item(self.promotion_channel_select)

        self.infraction_channel_select = discord.ui.ChannelSelect(
            placeholder="Demotion Channel",
            row=2,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=self.demotion_channel)]
        )
        self.infraction_channel_select.callback = self.infraction_channel
        self.add_item(self.infraction_channel_select)

        self.main_page = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Main Page",
            row=4
        )
        self.main_page.callback = self.main_page_callback
        self.add_item(self.main_page)

    async def main_page_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        await interaction.message.edit(embed=main_config_embed,view=Configuration(self.bot, interaction.user.id))
        await interaction.response.send_message("Main Page",ephemeral=True)

    async def enable_disable_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}

        staff_infraction_module = settings.get("staff_management", {})
        
        staff_infraction_module["enabled"] = not staff_infraction_module.get("enabled", False)
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="Enable/Disable Staff Infraction Module",
            value=f"""
            > Enable or Disable the Staff Infraction Module.\n Current Status: {'Enabled' if settings.get('staff_management', {}).get('enabled', False) else 'Disabled'}
            """
        )
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"Staff Infraction Module {'Enabled' if settings.get('staff_management', {}).get('enabled', False) else 'Disabled'}",ephemeral=True)

    async def promotion_channel(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "staff_management": {}}
        
        settings["staff_management"]["promotion_channel"] = self.promotion_channel_select.values[0].id
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            1,
            name="Promotion Channel",
            value=f"> Set the channel where you want to log promotions\n Current Channel: <#{self.promotion_channel_select.values[0].id}>"
        )
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("Promotion Channel Updated!",ephemeral=True)

    async def infraction_channel(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "staff_management": {}}
        
        settings["staff_management"]["demotion_channel"] = self.infraction_channel_select.values[0].id
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            2,
            name="Infraction Channel",
            value=f"> Set the channel where you want to log infractions.\n Current Channel: <#{self.infraction_channel_select.values[0].id}>"
        )
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("Infraction Channel Updated!",ephemeral=True)

class Configuration(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__()
        self.bot = bot
        self.user_id = user_id

        self.basic_settings_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Basic Setting",
            row=0
        )
        self.basic_settings_button.callback = self.basic_settings_callback
        self.add_item(self.basic_settings_button)

        self.anti_ping_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Anti Ping Module",
            row=0
        )
        self.anti_ping_button.callback = self.anti_ping_callback
        self.add_item(self.anti_ping_button)

        self.staff_infraction_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Staff Infraction Module",
            row=0
        )
        self.staff_infraction_button.callback = self.staff_infraction_callback
        self.add_item(self.staff_infraction_button)

        self.logging_channels_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Logging Channels",
            row=1
        )
        self.logging_channels_button.callback = self.logging_channels_callback
        self.add_item(self.logging_channels_button)

        self.other_configurations_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Other Configurations",
            row=1
        )
        self.other_configurations_button.callback = self.other_configurations_callback
        self.add_item(self.other_configurations_button)

    async def basic_settings_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        embed = discord.Embed(
            title="Basic Setting",
            description=" ",
            color=0x2F3136
        ).add_field(
            name="Staff Roles",
            value=f"""
            > These roles grant permission to use Cyni moderation commands.\n
            Current Roles: {"<@&" + ">, <@&".join([str(role) for role in settings.get("basic_settings", {}).get("staff_roles", [])]) + ">"}
            """,
            inline=False
        ).add_field(
            name="Management Roles",
            value=f"""
            > Users with these roles can utilize Cyni management commands, including Application Result commands, Staff Promo/Demo command, and setting the Moderation Log channel
            Current Roles: {"<@&" + ">, <@&".join([str(role) for role in settings.get("basic_settings", {}).get("management_roles", [])]) + ">"}
            """,
            inline=False
        )
        await interaction.message.edit(embed=embed, view=BasicConfiguration(self.bot,user_id=interaction.user.id))
        await interaction.response.send_message("Basic Settings Module",ephemeral=True)

    async def anti_ping_callback(self, interaction: discord.Interaction):
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        embed = discord.Embed(
            title="Anti Ping Module",
            description=" ",
            color=0x2F3136
        ).add_field(
            name="Enable/Disable Anti Ping",
            value=f"""
            > Enable or Disable the Anti Ping feature. When enabled, users will be warned if they ping the Anti Ping roles without having the bypass role.\n
            Current Status: {"Enabled" if settings.get("anti_ping_module", {}).get("enabled", False) else "Disabled"}
            """,
            inline=False
        ).add_field(
            name="Affected Roles",
            value=f"""
            > Users with these roles will be affected by the Anti Ping feature & if someone pings them without having the bypass role, bot will send a warning message.\n
            Current Roles: {"<@&" + ">, <@&".join([str(role) for role in settings.get("anti_ping_module", {}).get("affected_roles", [])]) + ">"}
            """,
            inline=False
        ).add_field(
            name="Bypass Roles",
            value=f"""
            > Users with these roles will be able to ping the Anti Ping roles without any warning message.\n
            Current Roles: {"<@&" + ">, <@&".join([str(role) for role in settings.get("anti_ping_module", {}).get("exempt_roles", [])]) + ">"}
            """,
            inline=False
        )
        await interaction.message.edit(embed=embed, view=AntiPingView(self.bot, interaction.user.id))
        await interaction.response.send_message("Anti Ping Module",ephemeral=True)

    async def staff_infraction_callback(self, interaction: discord.Interaction):
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        infraction_module = settings.get("staff_management", {})
        promotion_id = infraction_module.get("promotion_channel", 0)
        demotion_id = infraction_module.get("demotion_channel", 0)
        enalbed = infraction_module.get("enabled", False)

        embed = discord.Embed(
            title="Staff Infraction Module",
            description=" ",
            color=0x2F3136
        ).add_field(
            name="Enable/Disable Staff Infraction Module",
            value=f"> Enable or Disable the Staff Infraction Module.\n Current Status: {'Enabled' if enalbed else 'Disabled'}",
            inline=False
        ).add_field(
            name="Promotion Channel",
            value=f"> Set the channel where you want to log promotions\n Current Channel: <#{promotion_id}>",
            inline=False
        ).add_field(
            name="Infraction Channel",
            value=f"> Set the channel where you want to log infractions.\n Current Channel: <#{demotion_id}>",
            inline=False
        )
        await interaction.message.edit(embed=embed, view=StaffInfraction(self.bot, interaction.user.id,promo_channel=promotion_id,demotion_channel=demotion_id,enalbed=enalbed))

    async def logging_channels_callback(self, interaction: discord.Interaction):
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        moderation_log_channel = settings.get("logging_channels", {}).get("mod_log_channel", 0)
        staff_management_channel = settings.get("logging_channels", {}).get("application_channel", 0)
        ban_appeal_channel = settings.get("logging_channels", {}).get("ban_appeal_channel", 0)
        embed = discord.Embed(
            title="Logging Channels",
            description=" ",
            color=0x2F3136
        ).add_field(
            name="Moderation Log Channel",
            value=f"> Set the channel where you want to log moderation actions.\n Current Channel: <#{moderation_log_channel}>",
            inline=False
        ).add_field(
            name="Application Log Channel",
            value=f"> Set the channel where you want to log applications.,\n Current Channel: <#{staff_management_channel}>",
            inline=False
        ).add_field(
            name="Ban Appeal Log Channel",
            value=f"> Set the channel where you want to log ban appeals.,\n Current Channel: <#{ban_appeal_channel}>",
        )
        await interaction.message.edit(embed=embed, view=LoggingChannels(self.bot, interaction.user.id,moderation_log_channel,staff_management_channel,ban_appeal_channel))
        await interaction.response.send_message("Logging Channels",ephemeral=True)
        
    async def other_configurations_callback(self, interaction: discord.Interaction):
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        prefix = settings.get("customization", {}).get("prefix", "?")
        message_quota = settings.get("basic_settings", {}).get("message_quota", 0)
        embed = discord.Embed(
            title="Other Configurations",
            description=" ",
            color=0x2F3136
        ).add_field(
            name="Message Quota",
            value=f"> Set the message quota for your server.\nCurrent Message Quota: {message_quota}",
            inline=False
        ).add_field(
            name="Prefix",
            value=f"> Set the prefix for your server.\nCurrent Prefix: {prefix}",
            inline=False
        )
        await interaction.message.edit(embed=embed, view=OtherConfig(self.bot, interaction.user.id,prefix=prefix,message_quota=message_quota))
        await interaction.response.send_message("Other Configurations",ephemeral=True)

            
class AntiPingView(View):
    def __init__(self,bot,user_id:int):
        super().__init__()
        self.bot = bot
        self.user_id = user_id

        self.main_page = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Main Page",
            row=0
        )
        self.main_page.callback = self.main_page_callback
        self.add_item(self.main_page)

        self.enable_disable_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Enable/Disable Anti Ping",
            row=0
        )
        self.enable_disable_button.callback = self.enable_disable_callback
        self.add_item(self.enable_disable_button)

        self.affected_roles_button = discord.ui.RoleSelect(
            placeholder="Affected Roles",
            row=1,
            min_values=1,
            max_values=10,
        )
        self.affected_roles_button.callback = self.affected_roles_callback
        self.add_item(self.affected_roles_button)

        self.bypass_roles_button = discord.ui.RoleSelect(
            placeholder="Bypass Roles",
            row=2,
            min_values=1,
            max_values=10,
        )
        self.bypass_roles_button.callback = self.bypass_roles_callback
        self.add_item(self.bypass_roles_button)

    async def main_page_callback(self,interaction:discord.Interaction):
        await interaction.message.edit(embed=main_config_embed, view=Configuration(self.bot, interaction.user.id))
        await interaction.response.send_message("Main Page",ephemeral=True)

    async def enable_disable_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "anti_ping_module": {}}
        
        settings["anti_ping_module"]["enabled"] = not settings["anti_ping_module"].get("enabled",False)
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="Enable/Disable Anti Ping",
            value=f"""
            > Enable or Disable the Anti Ping feature. When enabled, users will be warned if they ping the Anti Ping roles without having the bypass role.\n
            Current Status: {"Enabled" if settings.get("anti_ping_module", {}).get("enabled", False) else "Disabled"}
            """
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
        
        settings["anti_ping_module"]["affected_roles"] = [role.id for role in self.affected_roles_button.values]
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            1,
            name="Affected Roles",
            value=f"""
            > Users with these roles will be affected by the Anti Ping feature & if someone pings them without having the bypass role, bot will send a warning message.\n
            Current Roles: {"<@&" + ">, <@&".join([str(role) for role in settings.get("anti_ping_module", {}).get("affected_roles", [])]) + ">"}
            """
        )
        await interaction.message.edit(
            embed=embed
        )
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
        
        settings["anti_ping_module"]["exempt_roles"] = [role.id for role in self.bypass_roles_button.values]
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            2,
            name="Bypass Roles",
            value=f"""
            > Users with these roles will be able to ping the Anti Ping roles without any warning message.\n
            Current Roles: {"<@&" + ">, <@&".join([str(role) for role in settings.get("anti_ping_module", {}).get("exempt_roles", [])]) + ">"}
            """
        )
        await interaction.message.edit(
            embed=embed
        )
        await interaction.response.send_message("Bypass Roles Updated!",ephemeral=True)

class BanAppealChannel(View):
    def __init__(self,bot,channel_id:int):
        super().__init__()
        self.bot = bot

        self.ban_appeal_channel = discord.ui.ChannelSelect(
            placeholder="Ban Appeal Log Channel",
            row=0,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=channel_id)]
        )
        self.ban_appeal_channel.callback = self.ban_appeal_channel_callback
        self.add_item(self.ban_appeal_channel)

    async def ban_appeal_channel_callback(self,interaction:discord.Interaction):
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "logging_channels": {}}
        try:
            settings["logging_channels"]["ban_appeal_channel"] = self.ban_appeal_channel.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "logging_channels": {"ban_appeal_channel": self.ban_appeal_channel.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        await interaction.response.send_message("Ban Appeal Log Channel Updated!",ephemeral=True)

class LoggingChannels(View):
    def __init__(self,bot,user_id:int,moderation_log_channel:int,staff_management_channel:int,ban_appeal_channel:int):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.moderation_log_channel = moderation_log_channel
        self.staff_management_channel = staff_management_channel
        self.ban_appeal_channel = ban_appeal_channel

        self.moderation_log_channel_select = discord.ui.ChannelSelect(
            placeholder="Moderation Log Channel",
            row=0,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=self.moderation_log_channel)]
        )
        self.moderation_log_channel_select.callback = self.moderation_log_channel_callback
        self.add_item(self.moderation_log_channel_select)

        self.staff_management_log_channel_select = discord.ui.ChannelSelect(
            placeholder="Application Log Channel",
            row=1,
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=self.staff_management_channel)]
        )
        self.staff_management_log_channel_select.callback = self.staff_management_log_channel_callback
        self.add_item(self.staff_management_log_channel_select)

        self.ban_appeal_channel = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Ban Appeal Log Channel",
            row=4
        )
        self.ban_appeal_channel.callback = self.ban_appeal_channel_callback
        self.add_item(self.ban_appeal_channel)

        self.main_page = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Main Page",
            row=4
        )
        self.main_page.callback = self.main_page_callback
        self.add_item(self.main_page)

    async def ban_appeal_channel_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        # Get the actual channel ID here
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            channel_id = settings.get("logging_channels", {}).get("ban_appeal_channel", 0)
        except KeyError:
            channel_id = 0
        view = BanAppealChannel(self.bot, channel_id)
        await interaction.response.send_message(
            "Select the channel where you want to log ban appeals.",
            ephemeral=True,
            view=view
        )

    async def main_page_callback(self,interaction:discord.Interaction):
        await interaction.message.edit(embed=main_config_embed, view=Configuration(self.bot, interaction.user.id))
        await interaction.response.send_message("Main Page",ephemeral=True)

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
            settings["logging_channels"]["mod_log_channel"] = self.moderation_log_channel_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "logging_channels": {"mod_log_channel": self.moderation_log_channel_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="Moderation Log Channel",
            value=f"> Set the channel where you want to log moderation actions.\n Current Channel: <#{self.moderation_log_channel_select.values[0].id}>"
        )

        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("Moderation Log Channel Updated!",ephemeral=True)

    async def staff_management_log_channel_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        try:
            settings["logging_channels"]["application_channel"] = self.staff_management_log_channel_select.values[0].id
        except KeyError:
            settings = {"_id": interaction.guild.id, "logging_channels": {"application_channel": self.staff_management_log_channel_select.values[0].id}}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            1,
            name="Application Log Channel",
            value=f"> Set the channel where you want to log applications.\n Current Channel: <#{self.staff_management_log_channel_select.values[0].id}>"
        )

        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("Staff Management Log Channel Updated!",ephemeral=True)

class PrefixModal(Modal):
    def __init__(self):
        super().__init__(title="Change Prefix", timeout=60)
        
        self.prefix_input = TextInput(
            placeholder="Enter your prefix",
            min_length=1,
            max_length=5,
            label="Prefix"
        )
        self.add_item(self.prefix_input)

    async def on_submit(self, interaction: discord.Interaction):
        settings = await interaction.client.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        if "customization" not in settings:
            settings["customization"] = {}
        
        settings["customization"]["prefix"] = self.prefix_input.value
        await interaction.client.settings.update({"_id": interaction.guild.id}, settings)
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            1,
            name="Prefix",
            value=f"> Set the prefix for your server.\nCurrent Prefix: {self.prefix_input.value}"
        )

        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"Your prefix is now {self.prefix_input.value}", ephemeral=True)
        self.stop()

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
        
        settings["basic_settings"]["message_quota"] = self.message_quota_input.value
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

class OtherConfig(View):
    def __init__(self, bot, user_id: int, prefix: str, message_quota: int):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.prefix = prefix
        self.message_quota = message_quota

        self.prefix_input = Button(
            style=discord.ButtonStyle.primary,
            label="Prefix",
            row=0
        )
        self.prefix_input.callback = self.prefix_callback
        self.add_item(self.prefix_input)

        self.message_quota_input = Button(
            style=discord.ButtonStyle.primary,
            label="Message Quota",
            row=0
        )
        self.message_quota_input.callback = self.message_quota_callback
        self.add_item(self.message_quota_input)

        self.main_page = Button(
            style=discord.ButtonStyle.primary,
            label="Main Page",
            row=0
        )
        self.main_page.callback = self.main_page_callback
        self.add_item(self.main_page)
    
    async def main_page_callback(self, interaction: discord.Interaction):
        await interaction.message.edit(embed=main_config_embed, view=Configuration(self.bot, interaction.user.id))
        await interaction.response.send_message("Main Page", ephemeral=True)

    async def prefix_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        await interaction.response.send_modal(PrefixModal())

    async def message_quota_callback(self,interaction:discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "You are not allowed to use this menu.", 
                ephemeral=True
            )
        
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id}
        await interaction.response.send_modal(MessageQuotaModal())