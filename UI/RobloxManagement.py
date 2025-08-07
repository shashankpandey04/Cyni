import discord
from utils.constants import BLANK_COLOR, GREEN_COLOR, RED_COLOR
from discord.ui import Button, View, Modal, TextInput

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

        # self.roblox_shift_config_button = Button(
        #     label="Configure Roblox Shift Settings",
        #     style=discord.ButtonStyle.secondary
        # )
        # self.roblox_shift_config_button.callback = self.roblox_shift_config_callback
        # self.add_item(self.roblox_shift_config_button)

        # self.roblox_punishment_button = Button(
        #     label="Configure Roblox Punishment Settings",
        #     style=discord.ButtonStyle.secondary
        # )
        # self.roblox_punishment_button.callback = self.roblox_punishment_callback
        # self.add_item(self.roblox_punishment_button)

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

    # async def roblox_shift_config_callback(self, interaction: discord.Interaction):
    #     """
    #     Opens the Roblox shift configuration modal.
    #     """
    #     await interaction.response.send_message(
    #         embed=discord.Embed(
    #             title="Roblox Shift Configuration",
    #             description="Configure the Roblox shift settings for your server.",
    #             color=BLANK_COLOR
    #         )
    #     )

    # async def roblox_punishment_callback(self, interaction: discord.Interaction):
    #     """
    #     Opens the Roblox punishment configuration modal.
    #     """
    #     await interaction.response.send_message(
    #         embed=discord.Embed(
    #             title="Roblox Punishment Configuration",
    #             description="Configure the Roblox punishment settings for your server.",
    #             color=BLANK_COLOR
    #         )
    #     )
