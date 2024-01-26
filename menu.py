import discord
import json
from utils import get_server_config

class SetupBot(discord.ui.Select):
    def __init__ (self):
      options = [
         discord.SelectOption(label="Staff Roles",description="Setup Staff Roles to work with Cyni",emoji="👮"),
         discord.SelectOption(label="Mod Log Channel",description="Setup Mod Log Channel to log moderation actions",emoji="📝"),
         discord.SelectOption(label="Server Config",description="View/Edit  Server Config",emoji="📜"),
         discord.SelectOption(label="Anti Ping Roles",description="Setup Anti Ping Roles",emoji="🔕"),
         discord.SelectOption(label="Support Server",description="Join Cyni Support Server",emoji="👥")
      ]
      super().__init__(placeholder="Setup Cyni",options=options,min_values=1,max_values=1)

    async def callback(self,interaction: discord.Interaction):
      if self.values[0] == "Staff Roles":
        embed = discord.Embed(title="Staff Roles",description="Setup Staff Roles to work with Cyni",color=0xFF00)
        await interaction.response.send_message(embed=embed,view=SelectStaffRoleView(),ephemeral=True)
      elif self.values[0] == "Mod Log Channel":
        await interaction.response.send_message("Select a channel where all the logs like warning,role addition,etc. will be logged.", view=ModLogView(),ephemeral=True)
      elif self.values[0] == "Anti Ping Roles":
        embed = discord.Embed(title="Anti Ping Roles",description="Setup Anti Ping Roles to work with Cyni",color=0xFF00)
        await interaction.response.send_message(embed=embed,view=AntiPingView(),ephemeral=True)
      elif self.values[0] == "Server Config":
        guild_id = str(interaction.guild.id)
        server_config = get_server_config(guild_id)
        staff_role_mentions = [f"<@&{role_id}>" for role_id in server_config['staff_roles']]
        management_role_mentions = [f"<@&{role_id}>" for role_id in server_config['management_role']]
        modlogchannel = f"<#{server_config['mod_log_channel']}>" if server_config['mod_log_channel'] != "null" else None
        embed = discord.Embed(
                    title="Server Config",
                    description=f"**Server Name:** {interaction.guild.name}\n**Server ID:** {interaction.guild.id}",
                    color=0x00FF00
              )
        if staff_role_mentions:
                  embed.add_field(name="Discord Staff Roles", value="Enabled", inline=False)
                  embed.add_field(name="**Discord Staff Roles:**", value='\n'.join(staff_role_mentions))
        else:
                  embed.add_field(name="Discord Staff Roles", value="Disabled")
        if management_role_mentions:
                  embed.add_field(name="Management Roles", value="Enabled", inline=False)
                  embed.add_field(name="**Management Roles:**", value='\n'.join(management_role_mentions))
        else:
                    embed.add_field(name="Management Roles", value="Disabled")
        if modlogchannel:
                    embed.add_field(name="Moeration Loging", value="Enabled", inline=False)
                    embed.add_field(name="**Mod Log Channel:**", value=modlogchannel)
        else:
                    embed.add_field(name="Moderation Loging", value="Disabled", inline=False)
        if 'premium' in server_config:
                    premium_status = "Enabled" if server_config['premium'] == 'true' else "Disabled"
                    embed.add_field(name="Premium Status", value=premium_status, inline=False)
        embed.color = discord.Color.red()
        await interaction.response.send_message(embed=embed,view=ChangeConfigView(),ephemeral=True)
      elif self.values[0] == "Support Server":
        embed = discord.Embed(title="Cyni Support",description="Need any help with Cyni?\nJoin support server.",color=0xFF00)
        await interaction.response.send_message(embed=embed, view=SupportBtn(),ephemeral=True)

class SetupView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(SetupBot())

class ChangeCofig(discord.ui.Select):
    def __init__ (self):
      options = [
         discord.SelectOption(label="Discord Staff Roles",description="Change Staff Roles",emoji="👮"),
         discord.SelectOption(label="Management Roles",description="Change Management Roles",emoji="🚨"),
         discord.SelectOption(label="Game Staff Roles",description="Change Game Staff Roles",emoji="🎮"),
         discord.SelectOption(label="Log Channel",description="Change Mod Log Channel",emoji="📝")
      ]
      super().__init__(placeholder="Change Server Config",options=options,min_values=1,max_values=1)
    async def callback(self,interaction: discord.Interaction):
      if self.values[0] == "Discord Staff Roles":
        await interaction.response.send_message(view=DiscordStaffRoles(),ephemeral=True)
      elif self.values[0] == "Management Roles":
        await interaction.response.send_message(view=ManagementRoleView(),ephemeral=True)
      elif self.values[0] == "Game Staff Roles":
        await interaction.response.send_message("This feature is disabled by Developers.",ephemeral=True)
      elif self.values[0] == "Log Channel":
        await interaction.response.send_message(view=ModLogView(),ephemeral=True)

class ChangeConfigView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(ChangeCofig())

class DiscordStaffRoleSelect(discord.ui.RoleSelect):
    def __init__ (self):
      super().__init__(placeholder="Select Discord Staff Roles",min_values=1,max_values=10)
    async def callback(self,interaction: discord.Interaction):
      try:
        await interaction.response.defer()
        response = [role.id for role in self.values]
        with open("server_config.json", "r") as file:
          server_config = json.load(file)
          guild_id = str(interaction.guild.id)
          server_config[guild_id]["staff_roles"] = response
        with open("server_config.json", "w") as file:
          json.dump(server_config, file, indent=4)
          embed = discord.Embed(description=f"Discod Staff Roles saved.",color=0x00FF00)
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
    def __init__ (self):
      super().__init__(placeholder="Select Management Roles",min_values=1,max_values=10)
    async def callback(self,interaction: discord.Interaction):
      try:
        await interaction.response.defer()
        response = [role.id for role in self.values]
        with open("server_config.json", "r") as file:
          server_config = json.load(file)
          guild_id = str(interaction.guild.id)
          server_config[guild_id]["management_role"] = response
        with open("server_config.json", "w") as file:
          json.dump(server_config, file, indent=4)
          embed = discord.Embed(description=f"Management Roles saved.",color=0x00FF00)
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
            with open("server_config.json", "r") as file:
                server_config = json.load(file)
                guild_id = str(interaction.guild.id)
                server_config[guild_id]["mod_log_channel"] = response
            with open("server_config.json", "w") as file:
                json.dump(server_config, file, indent=4, default=str)
            embed = discord.Embed(description=f"Mod Log Channel saved.", color=0x00FF00)
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
    def __init__ (self):
      options = [
        discord.SelectOption(label="Enable",description="Enable Anti Ping",emoji="🔕"),
        discord.SelectOption(label="Disable",description="Disable Anti Ping",emoji="🔔"),
        discord.SelectOption(label="Add Role",description="Add Anti Ping Role",emoji="🔒"),
        discord.SelectOption(label="Bypass Roles",description="Add Bypass Roles",emoji="🔓")
      ]
      super().__init__(placeholder="Anti Ping Options",options=options,min_values=1,max_values=1)
    async def callback(self,interaction: discord.Interaction):
      if self.values[0] == "Enable":
        with open("server_config.json", "r") as file:
          server_config = json.load(file)
          guild_id = str(interaction.guild.id)
          server_config[guild_id]["anti_ping"] = "true"
        with open("server_config.json", "w") as file:
          json.dump(server_config, file, indent=4)
          embed = discord.Embed(description=f"Anti Ping Enabled.",color=0x00FF00)
        await interaction.channel.send(embed=embed)
      elif self.values[0] == "Disable":
        with open("server_config.json", "r") as file:
          server_config = json.load(file)
          guild_id = str(interaction.guild.id)
          server_config[guild_id]["anti_ping"] = "false"
        with open("server_config.json", "w") as file:
          json.dump(server_config, file, indent=4)
          embed = discord.Embed(description=f"Anti Ping Disabled.",color=0x00FF00)
        await interaction.channel.send(embed=embed)
      elif self.values[0] == "Add Role":
        embed = discord.Embed(title="Anti Ping Roles",description="Setup Anti Ping Roles to work with Cyni",color=0xFF00)
        await interaction.response.send_message(embed=embed,view=AntiPingRoleView(),ephemeral=True)
      elif self.values[0] == "Bypass Roles":
        embed = discord.Embed(title="Anti Ping Bypass Roles",description="Setup Anti Ping Bypass Roles to work with Cyni",color=0xFF00)
        await interaction.response.send_message(embed=embed,view=AntiPingByPassView(),ephemeral=True)

class AntiPingView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(AntiPingOptions())

class AntiPingRoleSelect(discord.ui.RoleSelect):
    def __init__ (self,placeholder="Select Anti Ping Roles",min_values=1,max_values=10):
      super().__init__(placeholder=placeholder,min_values=min_values,max_values=max_values)
    async def callback(self,interaction:discord.Interaction):
      try:
        await interaction.response.defer()
        response = [role.id for role in self.values]
        with open("server_config.json", "r") as file:
          server_config = json.load(file)
          guild_id = str(interaction.guild.id)
          server_config[guild_id]["anti_ping_roles"] = response
        with open("server_config.json", "w") as file:
          json.dump(server_config, file, indent=4)
          embed = discord.Embed(description=f"Anti Ping Roles saved.",color=0x00FF00)
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
    def __init__ (self,placeholder="Select Anti Ping Bypass Roles",min_values=1,max_values=10):
      super().__init__(placeholder=placeholder,min_values=min_values,max_values=max_values)
    async def callback(self,interaction:discord.Interaction):
      try:
        await interaction.response.defer()
        response = [role.id for role in self.values]
        with open("server_config.json", "r") as file:
          server_config = json.load(file)
          guild_id = str(interaction.guild.id)
          server_config[guild_id]["bypass_antiping_roles"] = response
        with open("server_config.json", "w") as file:
          json.dump(server_config, file, indent=4)
          embed = discord.Embed(description=f"Anti Ping Bypass Roles saved.",color=0x00FF00)
        await interaction.channel.send(embed=embed)
        self.view.stop()
      except TimeoutError:
        await interaction.channel.send("Timed out. Please try again.")
        return

class AntiPingByPassView(discord.ui.View):
    def __init__ (self):
      super().__init__()
      self.add_item(AntiPingByPass())