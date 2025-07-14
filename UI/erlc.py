import discord
from utils.constants import BLANK_COLOR, GREEN_COLOR, RED_COLOR
from discord.ui import Button, View, Modal, TextInput

class StaffRoles(View):
    def __init__(self, bot, ctx):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        
        try:
            staff_roles = self.bot.erlc['staff_roles'] if 'staff_roles' in self.bot.erlc else []
            management_roles = self.bot.erlc['management_roles'] if 'management_roles' in self.bot.erlc else []
        except KeyError:
            staff_roles = []
            management_roles = []

        self.erlc_staff_roles = discord.ui.RoleSelect(
            placeholder="ERLC Staff Roles",
            row=1,
            min_values=1,
            max_values=10,
            default_values=[discord.Object(id=role_id) for role_id in staff_roles if role_id is not None]
        )
        self.erlc_staff_roles.callback = self.erlc_staff_roles_callback
        self.add_item(self.erlc_staff_roles)

        self.erlc_management_roles = discord.ui.RoleSelect(
            placeholder="ERLC Management Roles",
            row=2,
            min_values=1,
            max_values=10,
            default_values=[discord.Object(id=role_id) for role_id in management_roles if role_id is not None]
        )

        self.erlc_management_roles.callback = self.erlc_management_roles_callback
        self.add_item(self.erlc_management_roles)

    async def erlc_staff_roles_callback(self, interaction: discord.Interaction):
        selected_roles = [role.id for role in self.erlc_staff_roles.values]
        self.bot.erlc['staff_roles'] = selected_roles
        await self.bot.erlc.update({"_id": "erlc"}, {"$set": {"staff_roles": selected_roles}}, upsert=True)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ERLC Staff Roles Updated",
                description="The ERLC staff roles have been updated successfully.",
                color=GREEN_COLOR
            ),
            ephemeral=True
        )
        
    async def erlc_management_roles_callback(self, interaction: discord.Interaction):
        selected_roles = [role.id for role in self.erlc_management_roles.values]
        self.bot.erlc['management_roles'] = selected_roles
        await self.bot.erlc.update({"_id": "erlc"}, {"$set": {"management_roles": selected_roles}}, upsert=True)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ERLC Management Roles Updated",
                description="The ERLC management roles have been updated successfully.",
                color=GREEN_COLOR
            ),
            ephemeral=True
        )
