import discord
from utils import *

class SetupBot(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Staff Roles", description="Setup Staff Roles to work with Cyni", emoji="👮"),
            discord.SelectOption(label="Mod Log Channel", description="Setup Mod Log Channel to log moderation actions", emoji="📝"),
            discord.SelectOption(label="Server Config", description="View/Edit Server Config", emoji="📜"),
            discord.SelectOption(label="Anti Ping Roles", description="Setup Anti Ping Roles", emoji="🔕"),
            discord.SelectOption(label="Support Server", description="Join Cyni Support Server", emoji="👥")
        ]
        super().__init__(placeholder="Setup Cyni", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        option = self.values[0]
        if option == "Staff Roles":
            embed = discord.Embed(title="Staff Roles", description="Setup Staff Roles to work with Cyni", color=0xFF00)
            await interaction.response.send_message(embed=embed, view=SelectStaffRoleView(), ephemeral=True)
        elif option == "Mod Log Channel":
            await interaction.response.send_message("Select a channel where all the logs like warning, role addition, etc. will be logged.", view=ModLogView(), ephemeral=True)
        elif option == "Anti Ping Roles":
            embed = discord.Embed(title="Anti Ping Roles", description="Setup Anti Ping Roles to work with Cyni", color=0xFF00)
            await interaction.response.send_message(embed=embed, view=AntiPingView(), ephemeral=True)
        elif option == "Server Config":
            await display_server_config(interaction)
        elif option == "Support Server":
            embed = discord.Embed(title="Cyni Support", description="Need any help with Cyni?\nJoin support server.", color=0xFF00)
            await interaction.response.send_message(embed=embed, view=SupportBtn(), ephemeral=True)

class SetupView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(SetupBot())

class ChangeCofig(discord.ui.Select):
    def __init__ (self):
      options = [
         discord.SelectOption(label="Discord Staff Roles",description="Change Staff Roles",emoji="👮"),
         discord.SelectOption(label="Management Roles",description="Change Management Roles",emoji="🚨"),
         discord.SelectOption(label="Loa Role",description="Change Loa Role",emoji="🏝️"),
         discord.SelectOption(label="Log Channel",description="Change Mod Log Channel",emoji="📝"),
         discord.SelectOption(label="Staff Management Channel",description="Change Staff Management Channel",emoji="📝")
      ]
      super().__init__(placeholder="Change Server Config",options=options,min_values=1,max_values=1)
    async def callback(self,interaction: discord.Interaction):
      try:
        if self.values[0] == "Discord Staff Roles":
          await interaction.response.send_message(view=DiscordStaffRoles(),ephemeral=True)
        elif self.values[0] == "Management Roles":
          await interaction.response.send_message(view=ManagementRoleView(),ephemeral=True)
        elif self.values[0] == "Loa Role":
          await interaction.response.send_message(view=LoaRoleView() ,ephemeral=True)
        elif self.values[0] == "Log Channel":
          await interaction.response.send_message(view=ModLogView(),ephemeral=True),
        elif self.values[0] == "Staff Management Channel":
          await interaction.response.send_message(view=StaffManagementChannelView(),ephemeral=True)
      except TimeoutError:
        await interaction.response.send_message("Timed out. Please try again.")
        return
      
class ChangeConfigView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(ChangeCofig())

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
            option = self.values[0]

            guild_id = interaction.guild.id
            if option == "Enable":
                set_anti_ping_option(guild_id, True)
                await interaction.channel.send(embed=discord.Embed(description="Anti Ping Enabled.", color=0x00FF00))

            elif option == "Disable":
                set_anti_ping_option(guild_id, False)
                await interaction.channel.send(embed=discord.Embed(description="Anti Ping Disabled.", color=0x00FF00))

            elif option == "Add Role":
                embed = discord.Embed(title="Anti Ping Roles", description="Setup Anti Ping Roles to work with Cyni", color=0xFF00)
                await interaction.response.send_message(embed=embed, view=AntiPingRoleView(), ephemeral=True)

            elif option == "Bypass Roles":
                embed = discord.Embed(title="Anti Ping Bypass Roles", description="Setup Anti Ping Bypass Roles to work with Cyni", color=0xFF00)
                await interaction.response.send_message(embed=embed, view=AntiPingByPassView(), ephemeral=True)
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