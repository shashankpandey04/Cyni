import discord
from utils.constants import BLANK_COLOR, GREEN_COLOR, RED_COLOR
from discord.ui import Button, View, Modal, TextInput

class StaffRoles(View):
    def __init__(self, bot, ctx, sett):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.sett = sett
        try:
            staff_roles = self.sett.get('erlc', {}).get('staff_roles', [])
            management_roles = self.sett.get('erlc', {}).get('management_roles', [])
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
        
        # Update local settings
        self.sett['erlc']['staff_roles'] = selected_roles
        
        # Save to database
        await self.bot.settings.update({"_id": interaction.guild.id}, self.sett)
        
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
        
        # Update local settings
        self.sett['erlc']['management_roles'] = selected_roles
        
        # Save to database
        await self.bot.settings.update({"_id": interaction.guild.id}, self.sett)
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ERLC Management Roles Updated",
                description="The ERLC management roles have been updated successfully.",
                color=GREEN_COLOR
            ),
            ephemeral=True
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
        except KeyError:
            kill_logs_channel = None
            join_logs_channel = None

        self.kill_logs_channel = discord.ui.ChannelSelect(
            placeholder="Kill Logs Channel",
            row=1,
            channel_types=[discord.ChannelType.text],
            default_values=[discord.Object(id=kill_logs_channel)] if kill_logs_channel else []
        )

        self.join_logs_channel = discord.ui.ChannelSelect(
            placeholder="Join Logs Channel",
            row=2,
            channel_types=[discord.ChannelType.text],
            default_values=[discord.Object(id=join_logs_channel)] if join_logs_channel else []
        )

        self.add_item(self.kill_logs_channel)
        self.add_item(self.join_logs_channel)
        self.kill_logs_channel.callback = self.kill_logs_channel_callback
        self.join_logs_channel.callback = self.join_logs_channel_callback

    async def kill_logs_channel_callback(self, interaction: discord.Interaction):
        channel_id = self.kill_logs_channel.values[0].id if self.kill_logs_channel.values else None
        
        # Update local settings
        self.sett['erlc']['kill_logs_channel'] = channel_id
        
        # Save to database
        await self.bot.settings.update({"_id": interaction.guild.id}, self.sett)
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Kill Logs Channel Updated",
                description="The ERLC kill logs channel has been updated successfully.",
                color=GREEN_COLOR
            ),
            ephemeral=True
        )
        embed = discord.Embed(
            title="Kill Logs Channel",
            description=f"This channel will now log all ERLC kill actions.",
            color=GREEN_COLOR
        ).set_author(
            name="Cyni Bot",
            url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        await interaction.channel.send(embed=embed)

    async def join_logs_channel_callback(self, interaction: discord.Interaction):
        channel_id = self.join_logs_channel.values[0].id if self.join_logs_channel.values else None
        
        # Update local settings
        self.sett['erlc']['join_logs_channel'] = channel_id
        
        # Save to database
        await self.bot.settings.update({"_id": interaction.guild.id}, self.sett)
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Join Logs Channel Updated",
                description="The ERLC join logs channel has been updated successfully.",
                color=GREEN_COLOR
            ),
            ephemeral=True
        )

        embed = discord.Embed(
            title="Join Logs Channel",
            description=f"This channel will now log all ERLC join actions.",
            color=GREEN_COLOR
        ).set_author(
            name="Cyni Bot",
            url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        await interaction.channel.send(embed=embed)