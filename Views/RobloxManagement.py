import discord
from utils.constants import BLANK_COLOR, GREEN_COLOR, RED_COLOR
from discord.ui import Button, View, Modal, TextInput, Select, RoleSelect, ChannelSelect

class ModerationRoles(View):
    def __init__(self, bot, ctx, sett):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.sett = sett
        try:
            staff_roles = self.sett.get('roblox', {}).get('staff_roles', [])
            management_roles = self.sett.get('roblox', {}).get('management_roles', [])
        except KeyError:
            staff_roles = []
            management_roles = []

        self.roblox_staff_roles = discord.ui.RoleSelect(
            placeholder="Roblox Staff Roles",
            row=1,
            min_values=1,
            max_values=10,
            default_values=[discord.Object(id=role_id) for role_id in staff_roles if role_id is not None]
        )
        self.roblox_staff_roles.callback = self.roblox_staff_roles_callback
        self.add_item(self.roblox_staff_roles)

        self.roblox_management_roles = discord.ui.RoleSelect(
            placeholder="Roblox Management Roles",
            row=2,
            min_values=1,
            max_values=10,
            default_values=[discord.Object(id=role_id) for role_id in management_roles if role_id is not None]
        )

        self.roblox_management_roles.callback = self.roblox_management_roles_callback
        self.add_item(self.roblox_management_roles)

    async def roblox_staff_roles_callback(self, interaction: discord.Interaction):
        selected_roles = [role.id for role in self.roblox_staff_roles.values]

        if 'roblox' not in self.sett:
            self.sett['roblox'] = {}
        self.sett['roblox']['staff_roles'] = selected_roles
        
        await self.bot.settings.update({"_id": interaction.guild.id}, self.sett)
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Roblox Staff Roles Updated",
                description="The Roblox staff roles have been updated successfully.",
                color=GREEN_COLOR
            ),
            ephemeral=True
        )
        
    async def roblox_management_roles_callback(self, interaction: discord.Interaction):
        selected_roles = [role.id for role in self.roblox_management_roles.values]

        if 'roblox' not in self.sett:
            self.sett['roblox'] = {}
        self.sett['roblox']['management_roles'] = selected_roles
        
        await self.bot.settings.update({"_id": interaction.guild.id}, self.sett)
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Roblox Management Roles Updated",
                description="The Roblox management roles have been updated successfully.",
                color=GREEN_COLOR
            ),
            ephemeral=True
        )

class RobloxManagement(View):
    def __init__(self, bot, ctx, sett):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.sett = sett

        self.roblox_staff_roles_button = Button(
            label="Configure Roblox Moderation Roles",
            style=discord.ButtonStyle.secondary
        )
        self.roblox_staff_roles_button.callback = self.roblox_staff_roles_callback
        self.add_item(self.roblox_staff_roles_button)

        self.roblox_shift_config_button = Button(
            label="Configure Roblox Shift Settings",
            style=discord.ButtonStyle.secondary
        )
        self.roblox_shift_config_button.callback = self.roblox_shift_config_callback
        self.add_item(self.roblox_shift_config_button)

        self.roblox_punishment_button = Button(
            label="Configure Roblox Punishment Settings",
            style=discord.ButtonStyle.secondary
        )
        self.roblox_punishment_button.callback = self.roblox_punishment_callback
        self.add_item(self.roblox_punishment_button)

    async def roblox_staff_roles_callback(self, interaction: discord.Interaction):
        """
        Opens the Roblox staff roles configuration view.
        """
        view = ModerationRoles(self.bot, self.ctx, self.sett)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Roblox Moderation Roles Configuration",
                description="Select the roles that will be considered as Roblox staff and management.",
                color=BLANK_COLOR
            ),
            view=view,
            ephemeral=True
        )

    async def roblox_shift_config_callback(self, interaction: discord.Interaction):
        """
        Opens the Roblox shift configuration modal.
        """
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Roblox Shift Configuration",
                description="Configure the Roblox shift settings for your server.",
                color=BLANK_COLOR
            ),
            view=RobloxShiftConfig(self.bot, self.ctx, self.sett),
            ephemeral=True
        )

    async def roblox_punishment_callback(self, interaction: discord.Interaction):
        """
        Opens the Roblox punishment configuration modal.
        """
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Roblox Punishment Configuration",
                description="Configure the Roblox punishment settings for your server.",
                color=BLANK_COLOR
            )
        )

class OnBreakRoleConfig(View):
    def __init__(self, bot, ctx, sett):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.sett = sett

        try:
            on_break_role = self.sett["roblox"]["shift_module"].get("on_break_role")
        except KeyError:
            on_break_role = None

        self.on_break_role_select = RoleSelect(
            placeholder="Select the on-break role",
            min_values=0,
            max_values=1,
            row=0,
            default_values=[discord.Object(id=on_break_role)] if on_break_role else []
        )
        self.add_item(self.on_break_role_select)
        self.on_break_role_select.callback = self.on_break_role_callback

    async def on_break_role_callback(self, interaction: discord.Interaction):
        """
        Handles the on-break role selection.
        """
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You cannot configure this setting.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        settings = await self.bot.settings.find_by_id(interaction.guild.id)

        try:
            settings["roblox"]["shift_module"]["on_break_role"] = self.on_break_role_select.values[0].id
        except KeyError:
            settings["roblox"]["shift_module"] = {"on_break_role": self.on_break_role_select.values[0].id}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Roblox On-Break Role Configuration",
                description="Configure the Roblox on-break role for your server.",
                color=BLANK_COLOR
            ),
            ephemeral=True
        )

class RobloxShiftConfig(View):
    def __init__(self, bot, ctx, sett):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.sett = sett

        self.shift_log_channel_select = ChannelSelect(
            placeholder="Select the shift log channel",
            channel_types=[discord.ChannelType.text],
            row=0,
            max_values=1,
            min_values=0,
            default_values=[discord.Object(id=self.sett["roblox"]["shift_module"].get("channel"))] if self.sett["roblox"]["shift_module"].get("channel") else []
        )
        self.add_item(self.shift_log_channel_select)
        self.shift_log_channel_select.callback = self.shift_log_channel_callback

        self.on_duty_role_select = RoleSelect(
            placeholder="Select the on-duty role",
            min_values=0,
            row=1,
            default_values=[discord.Object(id=self.sett["roblox"]["shift_module"].get("on_duty_role"))] if self.sett["roblox"]["shift_module"].get("on_duty_role") else []
        )
        self.add_item(self.on_duty_role_select)
        self.on_duty_role_select.callback = self.on_duty_role_callback

        self.on_break_role_button = Button(
            label="Configure On-Break Role",
            style=discord.ButtonStyle.secondary,
            row=2
        )
        self.on_break_role_button.callback = self.on_break_role_callback
        self.add_item(self.on_break_role_button)

        # self.shift_types_button = Button(
        #     label="Configure Shift Types",
        #     style=discord.ButtonStyle.secondary,
        #     row=3
        # )
        # self.shift_types_button.callback = self.shift_types_callback
        # self.add_item(self.shift_types_button)

    async def shift_log_channel_callback(self, interaction: discord.Interaction):
        """
        Opens the Roblox shift log channel configuration modal.
        """
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You cannot configure this setting.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        try:
            settings["roblox"]["shift_module"]["channel"] = self.shift_log_channel_select.values[0].id
        except KeyError:
            settings["roblox"]["shift_module"] = {"channel": self.shift_log_channel_select.values[0].id}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Roblox Shift Log Channel Configuration",
                description="Configure the Roblox shift log channel for your server.",
                color=BLANK_COLOR
            ),
            ephemeral=True
        )

    async def on_duty_role_callback(self, interaction: discord.Interaction):
        """
        Opens the Roblox on-duty role configuration modal.
        """
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You cannot configure this setting.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        try:
            settings["roblox"]["shift_module"]["on_duty_role"] = self.on_duty_role_select.values[0].id
        except KeyError:
            settings["roblox"]["shift_module"]["on_duty_role"] = {"role": self.on_duty_role_select.values[0].id}
        await self.bot.settings.update({"_id": interaction.guild.id}, settings)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Roblox On-Duty Role Configuration",
                description="Configure the Roblox on-duty role for your server.",
                color=BLANK_COLOR
            ),
            ephemeral=True
        )

    async def on_break_role_callback(self, interaction: discord.Interaction):
        """
        Opens the Roblox on-break role configuration modal.
        """
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You cannot configure this setting.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Roblox On-Break Role Configuration",
                description="Configure the Roblox on-break role for your server.",
                color=BLANK_COLOR
            ),
            ephemeral=True,
            view=OnBreakRoleConfig(self.bot, self.ctx, self.sett)
        )

    # async def shift_types_callback(self, interaction: discord.Interaction):
    #     """
    #     Opens the Roblox shift types configuration modal.
    #     """
    #     await interaction.response.send_message(
    #         embed=discord.Embed(
    #             title="Roblox Shift Types Configuration",
    #             description="Configure the Roblox shift types for your server.",
    #             color=BLANK_COLOR
    #         )
    #     )
