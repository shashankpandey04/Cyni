import discord
from utils.constants import BLANK_COLOR, GREEN_COLOR, RED_COLOR
from discord.ui import Button, View, Modal, TextInput, Select, RoleSelect, ChannelSelect

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
        
        await self.bot.settings.update({"_id": interaction.guild.id}, {"$set": self.sett}, upsert=True)

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

        await self.bot.settings.update({"_id": interaction.guild.id}, {"$set": self.sett}, upsert=True)

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
                description=(
                    f"**Shift Log Channel**\n"
                    f"> Select the channel where shift logs will be sent.\n\n"
                    f"**On-Duty Role**\n"
                    f"> Select the role that will be assigned to users when they start a shift.\n\n"
                    f"**On-Break Role**\n"
                    f"> Select the role that will be assigned to users when they go on break."
                    # f"**Require Staff In-Game**\n"
                    # f"> Select whether staff members are required to be in-game to start a shift."
                ),
                color=BLANK_COLOR
            ),
            view=RobloxShiftConfig(self.bot, self.ctx, self.sett),
            ephemeral=True
        )

    async def roblox_punishment_callback(self, interaction: discord.Interaction):
        """
        Opens the Roblox punishment configuration modal.
        """
        view = RobloxSPunishmentConfig(self.bot, self.ctx, self.sett)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Roblox Punishment Configuration",
                description=(
                    f"**Toggle Roblox Punishments**\n"
                    f"> Enable or disable punishments logging for Roblox staff members.\n\n"
                    f"**Punishments Log Channel**\n"
                    f"> Select the channel where punishments will be logged.\n\n"
                    f"**Default Punishments**\n"
                    f"> Configure the default punishments for Roblox staff members."
                ),
                color=BLANK_COLOR
            ),
            view=view,
            ephemeral=True
        )

class RobloxOnBreakRoleConfig(View):
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
        if "roblox" not in settings:
            settings["roblox"] = {}
        if "shift_module" not in settings["roblox"]:
            settings["roblox"]["shift_module"] = {}
        settings["roblox"]["shift_module"]["on_break_role"] = self.on_break_role_select.values[0].id
        await self.bot.settings.update({"_id": interaction.guild.id}, {"$set": settings}, upsert=True)

        await interaction.response.send_message(
            embed=discord.Embed(
                description="The Roblox on-break role has been updated successfully.",
                color=GREEN_COLOR
            ),
            ephemeral=True
        )

class RobloxShiftConfig(View):
    def __init__(self, bot, ctx, sett):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.sett = sett

        self.shift_log_channel = self.sett["roblox"]["shift_module"].get("channel") if self.sett.get("roblox") and self.sett["roblox"].get("shift_module") else None

        self.shift_log_channel_select = ChannelSelect(
            placeholder="Select the shift log channel",
            channel_types=[discord.ChannelType.text],
            row=0,
            max_values=1,
            min_values=0,
            default_values=[discord.Object(id=self.shift_log_channel)] if self.shift_log_channel else []
        )
        self.add_item(self.shift_log_channel_select)
        self.shift_log_channel_select.callback = self.shift_log_channel_callback

        self.on_duty_role = self.sett["roblox"]["shift_module"].get("on_duty_role") if self.sett.get("roblox") and self.sett["roblox"].get("shift_module") else None

        self.on_duty_role_select = RoleSelect(
            placeholder="Select the on-duty role",
            min_values=0,
            row=1,
            default_values=[discord.Object(id=self.on_duty_role)] if self.on_duty_role else []
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

        self.shift_types_button = Button(
            label="Configure Shift Types",
            style=discord.ButtonStyle.secondary,
            row=2
        )
        self.shift_types_button.callback = self.shift_types_callback
        self.add_item(self.shift_types_button)

        # self.require_player_ingame_button = Button(
        #     label="Toggle Require Staff In-Game",
        #     style=discord.ButtonStyle.secondary,
        #     row=2
        # )
        # self.require_player_ingame_button.callback = self.require_player_ingame_callback
        # self.add_item(self.require_player_ingame_button)

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
        if "roblox" not in settings:
            settings["roblox"] = {}
        if "shift_module" not in settings["roblox"]:
            settings["roblox"]["shift_module"] = {}
        settings["roblox"]["shift_module"]["channel"] = self.shift_log_channel_select.values[0].id
        await self.bot.settings.update({"_id": interaction.guild.id}, {"$set": settings}, upsert=True)

        await interaction.response.send_message(
            embed=discord.Embed(
                description="Shift log channel has been updated successfully.",
                color=GREEN_COLOR
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
        if "roblox" not in settings:
            settings["roblox"] = {}
        if "shift_module" not in settings["roblox"]:
            settings["roblox"]["shift_module"] = {}
        settings["roblox"]["shift_module"]["on_duty_role"] = self.on_duty_role_select.values[0].id
        await self.bot.settings.update({"_id": interaction.guild.id}, {"$set": settings}, upsert=True)

        await interaction.response.send_message(
            embed=discord.Embed(
                description="The Roblox on-duty role has been updated successfully.",
                color=GREEN_COLOR
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
            view=RobloxOnBreakRoleConfig(self.bot, self.ctx, self.sett)
        )

    async def shift_types_callback(self, interaction: discord.Interaction):
        """
        Opens the Roblox shift types configuration modal.
        """
        shift_types = await self.bot.shift_types.find_by_id(interaction.guild.id) or {"_id": interaction.guild.id}

        embed = discord.Embed(
            title="Custom Shift Types",
            description="",
            color=BLANK_COLOR
        )
        if not shift_types or len(shift_types) == 1 and "_id" in shift_types:
            embed.description = "> No custom shift types found."
        else:
            for shift_name, shift_data in shift_types.items():
                if shift_name == "_id":
                    continue  # Skip the "_id" field
                embed.description += f"{shift_name}\n"
                if isinstance(shift_data, dict):  # Ensure shift_data is a dictionary
                    access_roles = shift_data.get('access_role', [])
                if not isinstance(access_roles, list):
                    access_roles = [access_roles]
                embed.description += f"> Access Roles: {', '.join([f'<@&{role_id}>' for role_id in access_roles])}\n"
        view = CustomShiftTypeMenu(self.bot, self.ctx)
        await interaction.response.send_message(
            embed=embed,
            view=view,
        )

    async def require_player_ingame_callback(self, interaction: discord.Interaction):
        """
        Toggles the require staff in-game setting.
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
        if "roblox" not in settings:
            settings["roblox"] = {}
        if "shift_module" not in settings["roblox"]:
            settings["roblox"]["shift_module"] = {}
        current_setting = settings["roblox"]["shift_module"].get("require_staff_ingame", False)
        new_setting = not current_setting
        settings["roblox"]["shift_module"]["require_staff_ingame"] = new_setting
        await self.bot.settings.update({"_id": interaction.guild.id}, {"$set": settings}, upsert=True)

        status = "Enabled" if new_setting else "Disabled"
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Require staff in-game has been `{status}`.",
                color=GREEN_COLOR
            ),
            ephemeral=True
        )
        
class RobloxSPunishmentConfig(View):
    def __init__(self, bot, ctx, sett):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.sett = sett
        try:
            self.punishment_enabled = self.sett["roblox"]["punishments"].get("enabled", False)
        except KeyError:
            self.punishment_enabled = False
        self.punishment_toggle = Select(
            placeholder="Select the punishment toggle",
            options=[
                discord.SelectOption(
                    label="Enabled",
                    value="true",
                    default=self.punishment_enabled
                ),
                discord.SelectOption(
                    label="Disabled",
                    value="false",
                    default=not self.punishment_enabled
                )
            ],
            row=0
        )
        self.add_item(self.punishment_toggle)
        self.punishment_toggle.callback = self.punishment_toggle_callback

        try:
            self.punishment_log_channel = self.sett["roblox"]["punishments"].get("channel")
        except KeyError:
            self.punishment_log_channel = None

        self.punishment_log_channel_select = ChannelSelect(
            placeholder="Select the punishment log channel",
            channel_types=[discord.ChannelType.text],
            row=1,
            max_values=1,
            min_values=0,
            default_values=[discord.Object(id=self.punishment_log_channel)] if self.punishment_log_channel else []
        )
        self.add_item(self.punishment_log_channel_select)
        self.punishment_log_channel_select.callback = self.punishment_log_channel_callback

        self.default_punishments_button = Button(
            label="Configure Default Punishments",
            style=discord.ButtonStyle.secondary,
        )
        self.add_item(self.default_punishments_button)
        self.default_punishments_button.callback = self.default_punishments_callback

    async def punishment_toggle_callback(self, interaction: discord.Interaction):
        """
        Toggles the punishment setting.
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

        self.punishment_enabled = self.punishment_toggle.values[0] == "true"
        settings = await self.bot.settings.find_by_id(interaction.guild.id)
        try:
            settings["roblox"]["punishments"]["enabled"] = self.punishment_enabled
        except KeyError:
            settings["roblox"]["punishments"] = {"enabled": self.punishment_enabled}
        await self.bot.settings.update({"_id": interaction.guild.id}, {"$set": settings}, upsert=True)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Success",
                description="The Roblox punishment setting has been updated.",
                color=GREEN_COLOR
            ),
            ephemeral=True
        )


    async def punishment_log_channel_callback(self, interaction: discord.Interaction):
        """
        Sets the punishment log channel.
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
            settings["roblox"]["punishments"]["channel"] = self.punishment_log_channel_select.values[0].id
        except KeyError:
            settings["roblox"]["punishments"] = {"channel": self.punishment_log_channel_select.values[0].id}
        await self.bot.settings.update({"_id": interaction.guild.id}, {"$set": settings}, upsert=True)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Success",
                description="The Roblox punishment log channel has been added to your server.",
                color=GREEN_COLOR
            ),
            ephemeral=True
        )

    async def default_punishments_callback(self, interaction: discord.Interaction):
        view = defaultPunishments(self.bot, self.sett, self.ctx.author.id)
        embed = discord.Embed(
            title="Default Punishments",
            description="Configure the default punishments for Roblox staff members.",
            color=BLANK_COLOR
        )
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )

class ReasonChangeModal(discord.ui.Modal):
    def __init__(self, bot, punishment_id):
        super().__init__(title="Change Punishment Reason")
        self.bot = bot
        self.punishment_id = punishment_id
        self.reason = None
        
        self.reason_input = discord.ui.TextInput(
            label="New Reason",
            placeholder="Enter the new reason here...",
            required=True,
            custom_id="reason"
        )
        self.add_item(self.reason_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        self.reason = self.reason_input.value
        
        await self.bot.punishments.update_one(
            {
                "snowflake": self.punishment_id,
                "guild_id": interaction.guild.id
            },
            {
                "$set": {
                    "reason": self.reason
                }
            }
        )
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Success",
                description="The punishment reason has been updated.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )
        
        self.stop()


class PunishmentManage(View):
    def __init__(self, bot, ctx, snowflake):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.punishment_id = snowflake

        self.change_reason_button = Button(
            label="Change Reason",
            style=discord.ButtonStyle.secondary
        )
        self.add_item(self.change_reason_button)
        self.change_reason_button.callback = self.change_reason_callback

        self.delete_button = Button(
            label="Delete Punishment",
            style=discord.ButtonStyle.danger
        )
        self.add_item(self.delete_button)
        self.delete_button.callback = self.delete_button_callback

    async def change_reason_callback(self, interaction: discord.Interaction):
        modal = ReasonChangeModal(self.bot, self.punishment_id)
        await interaction.response.send_modal(modal)
        await modal.wait()

    async def delete_button_callback(self, interaction: discord.Interaction):

        await self.bot.punishments.delete_one(
            {
                "snowflake": self.punishment_id,
                "guild_id": interaction.guild.id
            }
        )
        await interaction.message.edit(
            embed=discord.Embed(
                title="Success",
                description="The punishment has been deleted.",
                color=GREEN_COLOR
            ),
            view=None
        )

class defaultPunishments(discord.ui.View):
    def __init__(self, bot, sett, user_id):
        super().__init__()
        self.bot = bot
        self.sett = sett
        self.user_id = user_id

        self.default_punishments = ["warning", "kick", "ban", "bolo"]

        raw_punishments = {
            p["name"]: p.get("enabled", False)
            for p in sett.get("default_punishments", [])
        }

        self.warning_enabled = raw_punishments.get("warning", True)
        self.kick_enabled = raw_punishments.get("kick", True)
        self.ban_enabled = raw_punishments.get("ban", True)
        self.bolo_enabled = raw_punishments.get("bolo", True)

        options = [
            discord.SelectOption(label="Warning", value="Warning", default=self.warning_enabled),
            discord.SelectOption(label="Kick", value="Kick", default=self.kick_enabled),
            discord.SelectOption(label="Ban", value="Ban", default=self.ban_enabled),
            discord.SelectOption(label="BOLO", value="BOLO", default=self.bolo_enabled),
        ]
        select = discord.ui.Select(
            placeholder="Select a punishment",
            options=options,
            max_values=4,
        )

        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):

        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description="You are not authorized to change these settings.",
                    color=RED_COLOR
                ),
                ephemeral=True
            )

        selected = [i.lower() for i in interaction.data["values"]]

        setting = await self.bot.punishment_types.find_by_id(interaction.guild.id)
        if not setting:
            setting = {"_id": interaction.guild.id}

        setting["default_punishments"] = [
            {"name": name, "enabled": name in selected}
            for name in self.default_punishments
        ]

        # async def punishment_autocomplete(
        #     interaction: discord.Interaction, current: str
        # ) -> typing.List[app_commands.Choice[str]]:
        #     bot = interaction.client
        #     Data = await bot.punishment_types.find_by_id(interaction.guild.id)
        #     default_punishments = ["Warning", "Kick", "Ban", "Bolo"]
        #     enabled_punishments = None
        #     if Data is None:
        #         return [
        #             app_commands.Choice(name=item, value=item)
        #             for item in default_punishments
        #         ]
        #         enabled_punishments = Data.get("default_punishments", [])
        #     else:
        #         ndt = []
        #         for item in Data["types"]:
        #             if item not in default_punishments:
        #                 ndt.append(item)
        #         enabled_defaults = {
        #             p["name"].lower()
        #             for p in enabled_punishments
        #             if p.get("enabled", False)
        #         }
        #         filtered_punishments = [
        #             name.capitalize() for name in ["warning", "kick", "ban", "bolo"] if name in enabled_defaults
        #         ]
        #         return [
        #             app_commands.Choice(
        #                 name=(
        #                     item_identifier := item if isinstance(item, str) else item["name"]
        #                 ),
        #                 value=item_identifier,
        #             )
        #             for item in ndt + filtered_punishments
        #         ]


        await self.bot.punishment_types.update_one(
            {
                "_id": interaction.guild.id
            },
            {
                "$set": {
                    "default_punishments": setting["default_punishments"]
                }
            },
            upsert=True
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Default Punishments Updated",
                description="The default punishments have been updated.",
                color=GREEN_COLOR,
            ),
            ephemeral=True,
        )

class CreateShiftTypeMenu(discord.ui.View):
    def __init__(self, bot, ctx):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.sett = {}

        self.shift_name_modal = discord.ui.Button(
            label="Enter Shift Name",
            style=discord.ButtonStyle.secondary
        )
        self.add_item(self.shift_name_modal)
        self.shift_name_modal.callback = self.shift_name_modal_callback

        self.access_role_select = discord.ui.RoleSelect(
            placeholder="Select Access Role",
            min_values=1,
            max_values=5
        )
        self.add_item(self.access_role_select)
        self.access_role_select.callback = self.access_role_select_callback

        self.finish_button = discord.ui.Button(
            label="Finish",
            style=discord.ButtonStyle.primary
        )
        self.add_item(self.finish_button)
        self.finish_button.callback = self.finish_button_callback

    async def shift_name_modal_callback(self, interaction: discord.Interaction):

        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Missing Permissions",
                    description="You are not allowed to configure this shift.",
                    color=discord.Color.red()
                ), ephemeral=True
            )

        modal = CustomModal(
            "Shift Name Configuration",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Shift Name",
                        placeholder="Enter the name of the shift",
                        required=True,
                        max_length=100
                    )
                )
            ],
        )

        await interaction.response.send_modal(modal)
        
        if await modal.wait():
            return

        shift_name = modal.values.get("value")
        if not shift_name:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Alert Message Provided",
                    description="You must provide an alert message.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        self.sett["shift_name"] = shift_name

        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name="Shift Name", value=f"> {shift_name}", inline=False)
        await interaction.message.edit(embed=embed, view=self)

    async def access_role_select_callback(self, interaction: discord.Interaction):

        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Missing Permissions",
                    description="You are not allowed to configure this shift.",
                    color=discord.Color.red()
                ), ephemeral=True
            )
        
        selected_roles = self.access_role_select.values
        if not selected_roles:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Missing Information",
                    description="Please make sure all fields are filled out.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        self.sett["access_roles"] = selected_roles
        await interaction.response.defer()
        embed = interaction.message.embeds[0]
        embed.set_field_at(1, name="Access Roles", value=f"> {'<@&' + '>, <@&'.join([str(role.id) for role in selected_roles]) + '>' if selected_roles else 'N/A'}", inline=False)
        await interaction.message.edit(embed=embed, view=self)

    async def finish_button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Missing Permissions",
                    description="You are not allowed to configure this shift.",
                    color=discord.Color.red()
                ), ephemeral=True
            )

        selected_roles = self.access_role_select.values
        if not selected_roles:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Missing Information",
                    description="Please make sure all fields are filled out.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        await self.bot.shift_types.update_one(
            {
            "_id": interaction.guild.id
            },
            {
            "$set": {
                f"{self.sett['shift_name']}": {
                "access_role": [role.id for role in selected_roles]
                }
            }
            },
            upsert=True
        )

        embed = interaction.message.embeds[0]
        embed.title = "Shift Type Created"
        embed.description = f"Shift Name: {self.sett['shift_name']}\nAccess Roles: {', '.join([role.name for role in selected_roles])}"
        embed.color = discord.Color.green()
        embed.clear_fields()
        await interaction.response.edit_message(embed=embed, view=None)

class CustomShiftTypeMenu(discord.ui.View):
    def __init__(self, bot, ctx):
        super().__init__()
        self.bot = bot
        self.ctx = ctx

        self.create_shift_type_button = discord.ui.Button(
            label="Create/Edit Shift Type",
            style=discord.ButtonStyle.secondary
        )


        self.delete_shift_type_button = discord.ui.Button(
            label="Delete Shift Type",
            style=discord.ButtonStyle.danger
        )
        
        self.add_item(self.create_shift_type_button)
        self.add_item(self.delete_shift_type_button)

        self.create_shift_type_button.callback = self.create_shift_type_callback
        self.delete_shift_type_button.callback = self.delete_shift_type_callback

    async def create_shift_type_callback(self, interaction: discord.Interaction):
        view = CreateShiftTypeMenu(self.bot, self.ctx)
        embed = discord.Embed(
            title="Create New Shift Type",
            description="Please fill out the following form to create a new shift type.",
            color=discord.Color.blue()
        ).add_field(
            name="Shift Name",
            value="> N/A",
            inline=False
        ).add_field(
            name="Access Roles",
            value="> N/A",
            inline=False
        )
        await interaction.response.edit_message(view=view, embed=embed)

    async def delete_shift_type_callback(self, interaction: discord.Interaction):
        modal = CustomModal(
            "Shift Name Configuration",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Shift Name",
                        placeholder="Enter the name of the shift",
                        required=True,
                        max_length=100
                    )
                )
            ],
        )

        await interaction.response.send_modal(modal)
        
        if await modal.wait():
            return

        shift_name = modal.values.get("value")
        if not shift_name:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Alert Message Provided",
                    description="You must provide an alert message.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        await self.bot.shift_types.delete_one(
            {
                "_id": interaction.guild.id,
                f"{self.sett['shift_name']}": {
                    "$exists": True
                }
            }
        )

        embed = interaction.message.embeds[0]
        embed.title = "Shift Type Deleted"
        embed.description = f"Shift Name: {shift_name}"
        embed.color = discord.Color.red()
        embed.clear_fields()
        await interaction.response.edit_message(embed=embed, view=None)
