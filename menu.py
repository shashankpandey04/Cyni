import discord
from discord.ext import commands


from discord.ui import Button, View

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
        await interaction.message.edit(embed=main_config_embed,view=SetupBot(self.bot, interaction.user.id))
        await interaction.response.send_message("Main Page",ephemeral=True)

    async def staff_roles(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You are not allowed to use this menu.", ephemeral=True)
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "basic_settings": {}}
        
        settings["basic_settings"]["staff_roles"] = [role.id for role in self.staff_role_select.values]
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
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
        await interaction.message.edit(embed=embed, view=BasicConfiguration(self.bot, interaction.user.id))
        await interaction.response.send_message("Staff Roles Updated!",ephemeral=True)

    async def management_roles(self, interaction: discord.Interaction):
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        if not isinstance(settings, dict):
            settings = {"_id": interaction.guild.id, "basic_settings": {}}
        
        settings["basic_settings"]["management_roles"] = [role.id for role in self.management_role_select.values]
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)
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
        await interaction.message.edit(embed=embed, view=BasicConfiguration(self.bot, interaction.user.id))
        await interaction.response.send_message("Management Roles Updated!",ephemeral=True)

class SetupBot(discord.ui.View):
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
        embed = discord.Embed(
            title="Staff Infraction Module",
            description=" ",
            color=0x2F3136
        ).add_field(
            name="Promotion Channel",
            value="> Set the channel where you want to log promotions.",
            inline=False
        ).add_field(
            name="Infraction Channel",
            value="> Set the channel where you want to log infractions.",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

    async def logging_channels_callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Logging Channels",
            description=" ",
            color=0x2F3136
        ).add_field(
            name="Moderation Log Channel",
            value="> Set the channel where you want to log moderation actions.",
            inline=False
        ).add_field(
            name="Application Log Channel",
            value="> Set the channel where you want to log applications.",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

    async def other_configurations_callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Other Configurations",
            description=" ",
            color=0x2F3136
        ).add_field(
            name="Message Quota",
            value="> Set the message quota for your server.",
            inline=False
        ).add_field(
            name="Prefix",
            value="> Set the prefix for your server.",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

            
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
        await interaction.message.edit(embed=main_config_embed, view=SetupBot(self.bot, interaction.user.id))
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
        await interaction.message.edit(
            embed=embed, 
            view=AntiPingView(self.bot, interaction.user.id)
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
        await interaction.message.edit(
            embed=embed, 
            view=AntiPingView(self.bot, interaction.user.id)
        )
        await interaction.response.send_message("Bypass Roles Updated!",ephemeral=True)