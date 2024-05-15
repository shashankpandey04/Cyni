import discord
from utils import *
from db import mycon
from discord.ui import Button, View
from Modals.message_quota import MessageQuota
class ConfirmView(View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.success)
    async def yes_button(self, button: Button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label='No', style=discord.ButtonStyle.danger)
    async def no_button(self, button: Button, interaction: discord.Interaction):
        self.value = False
        self.stop()

async def display_server_config(interaction):
    try:
        cursor = mycon.cursor()
        guild_id = str(interaction.guild.id)
        cursor.execute("SELECT * FROM server_config WHERE guild_id = %s", (guild_id,))
        server_config = cursor.fetchone()
        if server_config:
            guild_id, staff_roles, management_roles, mod_log_channel, premium, report_channel, blocked_search, anti_ping, anti_ping_roles, bypass_anti_ping_roles, loa_role, staff_management_channel,infraction_channel,promotion_channel,prefix,application_channel,message_quota = server_config
            print(message_quota)
            embed = discord.Embed(
                title="Server Config",
                description=f"**Server Name:** {interaction.guild.name}\n**Server ID:** {guild_id}",
                color=0x00FF00
            )
            embed.add_field(name="Staff Roles", value=staff_roles if staff_roles else "Not set", inline=True)
            embed.add_field(name="Management Roles", value=management_roles if management_roles else "Not set", inline=True)
            embed.add_field(name="Mod Log Channel", value=f"<#{mod_log_channel}>" if mod_log_channel else "Not set", inline=True)
            embed.add_field(name="Premium", value="Enabled" if premium else "Disabled", inline=True)
            embed.add_field(name="Report Channel", value=f"<#{report_channel}>" if report_channel else "Not set", inline=True)
            #embed.add_field(name="Blocked Search", value=blocked_search if blocked_search else "Not set", inline=True)
            embed.add_field(name="Anti Ping", value="Enabled" if anti_ping else "Disabled", inline=True)
            embed.add_field(name="Anti Ping Roles", value=anti_ping_roles if anti_ping_roles else "Not set", inline=True)
            embed.add_field(name="Bypass Anti Ping Roles", value=bypass_anti_ping_roles if bypass_anti_ping_roles else "Not set", inline=True)
            #embed.add_field(name="Loa Role", value=loa_role if loa_role else "Not set", inline=True)
            #embed.add_field(name="Staff Management Channel", value=f"<#{staff_management_channel}>" if staff_management_channel else "Not set", inline=True)
            embed.add_field(name="Infraction Channel", value=f"<#{infraction_channel}>" if infraction_channel else "Not set", inline=True)
            embed.add_field(name="Promotion Channel", value=f"<#{promotion_channel}>" if promotion_channel else "Not set", inline=True)
            embed.add_field(name="Prefix", value=prefix if prefix else "?", inline=True)
            embed.add_field(name="Application Channel", value=f"<#{application_channel}>" if application_channel else "Not set", inline=True)
            embed.add_field(name="Message Quota", value=message_quota if message_quota else "Not set", inline=True)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Server config not found.", ephemeral=True)
    except Exception as e:
        print(f"An error occurred while fetching server config: {e}")
    finally:
        cursor.close()

class SetupBot(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Staff Management", description="Manage Staff to work with Cyni", emoji="👮"),
            discord.SelectOption(label="Server Config", description="View/Edit Server Config", emoji="📜"),
            discord.SelectOption(label="Anti Ping", description="Setup Anti Ping Roles", emoji="🔕"),
            discord.SelectOption(label="Staff Management Channel", description="Select Staff Management Channel", emoji="📝"),
            discord.SelectOption(label="Message Quota", description="Set Message Quota", emoji="📝")
        ]
        super().__init__(placeholder="Setup Cyni", options=options, min_values=1, max_values=1)

    async def callback(self,interaction: discord.Interaction):
        if self.values[0] == "Staff Management":
            embed = discord.Embed(title="Staff Roles",description="Setup Staff Roles to work with Cyni",color=0xFF00)
            await interaction.response.send_message(embed=embed,view=SelectStaffRoleView(),ephemeral=True)
        elif self.values[0] == "Mod Log Channel":
            await interaction.response.send_message("Select a channel where all the logs like warning,role addition,etc. will be logged.", view=ModLogView(),ephemeral=True)
        elif self.values[0] == "Anti Ping":
            embed = discord.Embed(title="Anti Ping Roles",description="Setup Anti Ping Roles to work with Cyni",color=0xFF00)
            await interaction.response.send_message(embed=embed,view=AntiPingView(),ephemeral=True)
        elif self.values[0] == "Server Config":
            await display_server_config(interaction)
        elif self.values[0] == "Staff Management Channel":
            await interaction.response.send_message(view=SelectChannelsView(),ephemeral=True)
        elif self.values[0] == "Message Quota":
            await interaction.response.send_modal(MessageQuota())

class SetupView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(SetupBot())

class DiscordStaffRoleSelect(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder="Select Discord Staff Roles", min_values=1, max_values=10)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            response = [role.id for role in self.values]
            guild_id = interaction.guild.id
            save_staff_roles(guild_id, response)

            embed = discord.Embed(description="Discord Staff Roles saved.", color=0x00FF00)
            await interaction.channel.send(embed=embed)
            self.view.stop()
        except TimeoutError:
            await interaction.channel.send("Timed out. Please try again.")
            return

class DiscordStaffRoles(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(DiscordStaffRoleSelect())

class ManagementRoleSelect(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder="Select Management Roles", min_values=1, max_values=10)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            response = [role.id for role in self.values]
            guild_id = interaction.guild.id
            save_management_roles(guild_id, response)

            embed = discord.Embed(description="Management Roles saved.", color=0x00FF00)
            await interaction.channel.send(embed=embed)
            self.view.stop()
        except TimeoutError:
            await interaction.channel.send("Timed out. Please try again.")
            return

class ManagementRoleView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(ManagementRoleSelect())

class SelectStaffRoleSelect(discord.ui.Select):
    def __init__ (self):
      options = [
         discord.SelectOption(label="Discord Staff Roles",description="Select Staff Roles",emoji="👮"),
         discord.SelectOption(label="Management Roles",description="Select Management Roles",emoji="🚨")
      ]
      super().__init__(placeholder="Select Staff Roles",options=options,min_values=1,max_values=1)
    async def callback(self,interaction: discord.Interaction):
      if self.values[0] == "Discord Staff Roles":
        await interaction.response.send_message(view=DiscordStaffRoles(),ephemeral=True)
      elif self.values[0] == "Management Roles":
        await interaction.response.send_message(view=ManagementRoleView(),ephemeral=True)

class SelectStaffRoleView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(SelectStaffRoleSelect())

class ModLogBot(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder="Select Mod Log Channel")
    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            response = self.values[0].id if self.values else None
            guild_id = interaction.guild.id
            save_mod_log_channel(guild_id, response)
            embed = discord.Embed(description="Mod Log Channel saved.", color=0x00FF00)
            await interaction.channel.send(embed=embed)
            self.view.stop()
        except TimeoutError:
            await interaction.channel.send(f"{interaction.user.mention} Timed out. Please try again.")
            return

class ModLogView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(ModLogBot())   

class SupportBtn(discord.ui.View):
    def __init__ (self,inv="https://discord.gg/2D29TSfNW6"):
      super().__init__()
      self.inv=inv
      self.add_item(discord.ui.Button(label='Support Server',url='https://discord.gg/2D29TSfNW6'))
    async def support(self,interaction:discord.Interaction,button:discord.ui.Button):
       await interaction.response.send_message(self.inv,ephemeral=True)

class AntiPingOptions(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Enable", description="Enable Anti Ping", emoji="🔕"),
            discord.SelectOption(label="Disable", description="Disable Anti Ping", emoji="🔔"),
            discord.SelectOption(label="Add Role", description="Add Anti Ping Role", emoji="🔒"),
            discord.SelectOption(label="Bypass Roles", description="Add Bypass Roles", emoji="🔓")
        ]
        super().__init__(placeholder="Anti Ping Options", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            guild_id = interaction.guild.id
            if self.values[0] == "Enable":
                set_anti_ping_option(guild_id, True)
                await interaction.channel.send(embed=discord.Embed(description="Anti Ping Enabled.", color=0x00FF00))
            elif self.values[0] == "Disable":
                set_anti_ping_option(guild_id, False)
                await interaction.channel.send(embed=discord.Embed(description="Anti Ping Disabled.", color=0x00FF00))
            elif self.values[0] == "Add Role":
                embed = discord.Embed(title="Anti Ping Roles", description="Setup Anti Ping Roles to work with Cyni", color=0xFF00)
                await interaction.channel.send(embed=embed, view=AntiPingRoleView(),ephemeral=True)
            elif self.values[0] == "Bypass Roles":
                embed = discord.Embed(title="Anti Ping Bypass Roles", description="Setup Anti Ping Bypass Roles to work with Cyni", color=0xFF00)
                await interaction.channel.send(embed=embed, view=AntiPingByPassView(),ephemeral=True)
        except Exception as e:
            print(f"An error occurred: {e}")

class AntiPingView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(AntiPingOptions())

class AntiPingRoleSelect(discord.ui.RoleSelect):
    def __init__(self, placeholder="Select Anti Ping Roles", min_values=1, max_values=10):
        super().__init__(placeholder=placeholder, min_values=min_values, max_values=max_values)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            response = [role.id for role in self.values]
            guild_id = interaction.guild.id
            save_anti_ping_roles(guild_id, response)
            
            embed = discord.Embed(description="Anti Ping Roles saved.", color=0x00FF00)
            await interaction.channel.send(embed=embed)
            self.view.stop()
        except TimeoutError:
            await interaction.channel.send("Timed out. Please try again.")
            return

class AntiPingRoleView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(AntiPingRoleSelect())

class AntiPingByPass(discord.ui.RoleSelect):
    def __init__(self, placeholder="Select Anti Ping Bypass Roles", min_values=1, max_values=10):
        super().__init__(placeholder=placeholder, min_values=min_values, max_values=max_values)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            response = [role.id for role in self.values]
            guild_id = interaction.guild.id
            save_anti_ping_bypass_roles(guild_id, response)

            embed = discord.Embed(description="Anti Ping Bypass Roles saved.", color=0x00FF00)
            await interaction.channel.send(embed=embed)
            self.view.stop()
        except TimeoutError:
            await interaction.channel.send("Timed out. Please try again.")
            return

class AntiPingByPassView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(AntiPingByPass())

class LoaRoleSelect(discord.ui.RoleSelect):
    def __init__(self, placeholder="Select Loa Roles", min_values=1, max_values=10):
        super().__init__(placeholder=placeholder, min_values=min_values, max_values=max_values)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            response = [role.id for role in self.values]
            guild_id = interaction.guild.id
            save_loa_roles(guild_id, response)

            embed = discord.Embed(description="Loa Roles saved.", color=0x00FF00)
            await interaction.channel.send(embed=embed)
            self.view.stop()
        except TimeoutError:
            await interaction.channel.send("Timed out. Please try again.")
            return

class LoaRoleView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(LoaRoleSelect())
    
class StaffManagementChannelView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(StaffManagementChannel())

class StaffManagementChannel(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder="Select Staff Management Channel")

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            response = self.values[0].id if self.values else None
            guild_id = interaction.guild.id
            save_staff_management_channel(guild_id, response)
            
            embed = discord.Embed(description="Staff Management Channel saved.", color=0x00FF00)
            await interaction.channel.send(embed=embed)
            self.view.stop()
        except TimeoutError:
            await interaction.channel.send(f"{interaction.user.mention} Timed out. Please try again.")
            return
        
class VoteView(discord.ui.View):
    def __init__ (self,inv="https://discord.gg/2D29TSfNW6"):
      self.inv = inv
      super().__init__()
      self.add_item(discord.ui.Button(label='Top.gg',url='https://top.gg/bot/1136945734399295538/vote'))
    async def support(self,interaction:discord.Interaction,button:discord.ui.Button):
       await interaction.response.send_message(self.inv,ephemeral=True)

class SelectChannelsView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(SelectChannels())

class SelectChannels(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Infraction Channel", description="Select Infraction Channel", emoji="📝"),
            discord.SelectOption(label="Promotion Channel", description="Select Promotion Channel", emoji="📝"),
            discord.SelectOption(label="Log Channel", description="Select Mod Log Channel", emoji="📝"),
            discord.SelectOption(label="Application Channel", description="Select Application Channel", emoji="📝")
        ]
        super().__init__(placeholder="Select Category", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)  # Make the response ephemeral
            if self.values[0] == "Infraction Channel":
                await interaction.channel.send(view=InfractionChannelView())
            elif self.values[0] == "Promotion Channel":
                await interaction.channel.send(view=PromotionChannelView())
            elif self.values[0] == "Log Channel":
                await interaction.channel.send(view=ModLogView())
            elif self.values[0] == "Application Channel":
                await interaction.channel.send(view=ApplicationChannelView())
        except TimeoutError:
            await interaction.channel.send("Timed out. Please try again.")
            return

class InfractionChannelView(discord.ui.View):
    def __init__ (self):
        super().__init__()
        self.add_item(InfractionChannel())

class InfractionChannel(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder="Select Infraction Channel")

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            response = self.values[0].id if self.values else None
            guild_id = interaction.guild.id
            save_infraction_channel(guild_id, response)

            embed = discord.Embed(description="Infraction Channel saved.", color=0x00FF00)
            await interaction.channel.send(embed=embed)
            self.view.stop()
        except TimeoutError:
            await interaction.channel.send(f"{interaction.user.mention} Timed out. Please try again.")
            return

class PromotionChannelView(discord.ui.View):
    def __init__ (self):
        super().__init__()
        self.add_item(PromotionChannel())

class PromotionChannel(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder="Select Promotion Channel")

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            response = self.values[0].id if self.values else None
            guild_id = interaction.guild.id
            save_promotion_channel(guild_id, response)

            embed = discord.Embed(description="Promotion Channel saved.", color=0x00FF00)
            await interaction.channel.send(embed=embed)
            self.view.stop()
        except TimeoutError:
            await interaction.channel.send(f"{interaction.user.mention} Timed out. Please try again.")
            return
        
class ApplicationChannelView(discord.ui.View):
    def __init__ (self):
        super().__init__()
        self.add_item(ApplicationChannel())

class ApplicationChannel(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder="Select Application Channel")

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            response = self.values[0].id if self.values else None
            guild_id = interaction.guild.id
            save_application_channel(guild_id, response)

            embed = discord.Embed(description="Application Channel saved.", color=0x00FF00)
            await interaction.channel.send(embed=embed)
            self.view.stop()
        except TimeoutError:
            await interaction.channel.send(f"{interaction.user.mention} Timed out. Please try again.")
            return