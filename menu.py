import discord
from utils import *
from db import mycon
from discord.ui import Button, View
from Modals.message_quota import MessageQuota
from Modals.prefix import Prefix
from utils import *

class ConfirmView(View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.success)
    async def yes_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_message("Action Performed Successfully.")
        self.value = True
        self.stop()

    @discord.ui.button(label='No', style=discord.ButtonStyle.danger)
    async def no_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_message("Action Canceled.")
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
            
            def convert_roles(role_list):
                if not role_list:
                    return None
                
                roles = [int(role.strip()) for role in role_list.strip('][').split(',') if role.strip().isdigit()]
                valid_roles = [role for role in roles if interaction.guild.get_role(role)]
                
                return valid_roles
            
            staff_roles = convert_roles(staff_roles)
            management_roles = convert_roles(management_roles)

            embed = discord.Embed(
                title="Server Config",
                description=f"**Server Name:** {interaction.guild.name}\n**Server ID:** {guild_id}",
                color=0x2F3136
            ).add_field(
                name="Discord Staff Roles", 
                value=", ".join([f"<@&{role}>" for role in staff_roles]) if staff_roles else "Not set",
                inline=True
            ).add_field(
                name="Management Roles", 
                value=", ".join([f"<@&{role}>" for role in management_roles]) if management_roles else "Not set",
                inline=True
            ).add_field(
                name="Mod Log Channel", 
                value=f"<#{mod_log_channel}>" if mod_log_channel else "Not set", 
                inline=True
            ).add_field(
                name="Premium", 
                value="Enabled" if premium else "Disabled", 
                inline=True
            ).add_field(
                name="Report Channel", 
                value=f"<#{report_channel}>" if report_channel else "Not set", 
                inline=True
            )
            #embed.add_field(name="Blocked Search", value=blocked_search if blocked_search else "Not set", inline=True)
            embed.add_field(name="Anti Ping", value="Enabled" if anti_ping else "Disabled", inline=True)
            embed.add_field(name="Anti Ping Roles", value=anti_ping_roles if anti_ping_roles else "Not set", inline=True)
            embed.add_field(name="Bypass Anti Ping Roles", value=bypass_anti_ping_roles if bypass_anti_ping_roles else "Not set", inline=True)
            #embed.add_field(name="Loa Role", value=loa_role if loa_role else "Not set", inline=True)
            #embed.add_field(name="Staff Management Channel", value=f"<#{staff_management_channel}>" if staff_management_channel else "Not set", inline=True)
            embed.add_field(name="Infraction Channel", value=f"<#{infraction_channel}>" if infraction_channel else "Not set", inline=True)
            embed.add_field(name="Promotion Channel", value=f"<#{promotion_channel}>" if promotion_channel else "Not set", inline=True)
            embed.add_field(name="Prefix", value=prefix if prefix else "?", inline=True)
            embed.add_field(name="Ban Appeal Channel", value=f"<#{application_channel}>" if application_channel else "Not set", inline=True)
            embed.add_field(name="Message Quota", value=message_quota if message_quota else "Not set", inline=True)
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.send(embed=embed)
        else:
            try:
                await interaction.response.send_message("Server config not found.", ephemeral=True)
            except:
                await interaction.send("Server config not found.")
    except Exception as e:
        print(f"An error occurred while fetching server config: {e}")
    finally:
        cursor.close()

class SetupBot(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Basic Setting", 
                description="Manage Staff & Management Roles", 
                emoji="👮"
            ),
            discord.SelectOption(
                label="Anti Ping Module", 
                description="Setup Anti Ping Roles",
                emoji="🔕"
            ),
            discord.SelectOption(
                label="Staff Infraction Module", 
                description="Setup Staff Infraction Module to Promote & Demote your Staff.", 
                emoji="🚨"
            ),
            discord.SelectOption(
                label="Logging Channels", 
                description="Set Application Log Channel, Moderation Log Channel for your server.", 
                emoji="📝"
            ),
            discord.SelectOption(
                label="Other Configurations",
                description="Set Message Quota & Prefix",
                emoji="🔧"
            )
        ]
        super().__init__(placeholder="Manage Server Settings", options=options, min_values=1, max_values=1)

    async def callback(self,interaction: discord.Interaction):
        if self.values[0] == "Basic Setting":
            embed = discord.Embed(
                title="Basic Setting",
                description=" ",
                color=0x2F3136
            ).add_field(
                name="Staff Roles",
                value="> These roles grant permission to use Cyni moderation commands.",
                inline=False
            ).add_field(
                name="Management Roles",
                value="> Users with these roles can utilize Cyni management commands, including Application Result commands, Staff Promo/Demo command, and setting the Moderation Log channel",
                inline=False
            )
            await interaction.response.send_message(embed=embed,view=BasicConfiguration(staff_roles=get_staff_roles(interaction.guild.id), management_roles=get_management_roles(interaction.guild.id)),ephemeral=True)
        elif self.values[0] == "Anti Ping Module":
            embed = discord.Embed(
                title="Anti Ping Module",
                description=" ",
                color=0x2F3136
            ).add_field(
                name="Enable/Disable Anti Ping",
                value=f"> Enable or Disable the Anti Ping feature. When enabled, users will be warned if they ping the Anti Ping roles without having the bypass role.\n\nCurrent Status: {'Enabled' if get_anti_ping_option(interaction.guild.id) else 'Disabled'}",
                inline=False
            ).add_field(
                name="Affected Roles",
                value="> Users with these roles will be affected by the Anti Ping feature & if someone pings them without having the bypass role, bot will send a warning message.",
                inline=False
            ).add_field(
                name="Bypass Roles",
                value="> Users with these roles will be able to ping the Anti Ping roles without any warning message.",
                inline=False
            )
            await interaction.response.send_message(embed=embed,view=AntiPingConfiguration(anti_ping_roles=get_anti_ping_roles(interaction.guild.id), bypass_anti_ping_roles=get_anti_ping_bypass_roles(interaction.guild.id)),ephemeral=True)
        elif self.values[0] == "Staff Infraction Module":
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
            await interaction.response.send_message(embed=embed,view=PromotionDemotionLogs(promotion_channel_id=get_promotion_channel(interaction.guild.id),infraction_channel_id=get_infraction_channel(interaction.guild.id)),ephemeral=True)
        elif self.values[0] == "Logging Channels":
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
            await interaction.response.send_message(embed=embed,view=ApplicationAndModLogView(application_channel_id=get_application_channel(interaction.guild.id),mod_log_channel_id=get_mod_log_channel(interaction.guild.id)),ephemeral=True)
        elif self.values[0] == "Other Configurations":
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
            await interaction.response.send_message(embed=embed,view=MessageQuotaAndPrefixView(message_quota=get_message_quota(interaction.guild.id),prefix=get_prefix(interaction.guild.id)),ephemeral=True)

class SetupView(View):
    def __init__(self):
        super().__init__()
        self.add_item(SetupBot())

class SupportBtn(discord.ui.View):
    def __init__ (self,inv="https://discord.gg/2D29TSfNW6"):
      super().__init__()
      self.inv=inv
      self.add_item(discord.ui.Button(label='Support Server',url='https://discord.gg/2D29TSfNW6'))
    async def support(self,interaction:discord.Interaction,button:discord.ui.Button):
       await interaction.response.send_message(self.inv,ephemeral=True)

class VoteView(discord.ui.View):
    def __init__ (self,inv="https://discord.gg/2D29TSfNW6"):
      self.inv = inv
      super().__init__()
      self.add_item(discord.ui.Button(label='Top.gg',url='https://top.gg/bot/1136945734399295538/vote'))
    async def support(self,interaction:discord.Interaction,button:discord.ui.Button):
       await interaction.response.send_message(self.inv,ephemeral=True)


class BasicConfiguration(View):
    def __init__(self, staff_roles=None, management_roles=None):
        super().__init__()
        self.staff_role_select = discord.ui.RoleSelect(
            placeholder="Staff Roles",
            row=0,
            min_values=1,
            max_values=10,
            default_values=[discord.Object(id=role) for role in staff_roles] if staff_roles else []
        )
        self.staff_role_select.callback = self.staff_roles
        self.add_item(self.staff_role_select)

        self.management_role_select = discord.ui.RoleSelect(
            placeholder="Management Roles",
            row=1,
            min_values=1,
            max_values=10,
            default_values=[discord.Object(id=role) for role in management_roles] if management_roles else []
        )
        self.management_role_select.callback = self.management_roles
        self.add_item(self.management_role_select)

    async def staff_roles(self, interaction: discord.Interaction):
        response = [role.id for role in self.staff_role_select.values]
        guild_id = interaction.guild.id
        save_staff_roles(guild_id, response)
        embed = discord.Embed(description="Staff Roles saved.", color=0x2F3136)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def management_roles(self, interaction: discord.Interaction):
        response = [role.id for role in self.management_role_select.values]
        guild_id = interaction.guild.id
        save_management_roles(guild_id, response)
        embed = discord.Embed(description="Management Roles saved.", color=0x2F3136)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AntiPingConfiguration(View):
    def __init__(self, anti_ping_roles=None, bypass_anti_ping_roles=None):
        super().__init__()
        
        self.anti_ping_enable = discord.ui.Button(
            label="Anti Ping Enable/Disable",
            style=discord.ButtonStyle.primary,
            row=0
        )
        self.anti_ping_enable.callback = self.anti_ping_enable_callback
        self.add_item(self.anti_ping_enable)

        self.anti_ping_role_select = discord.ui.RoleSelect(
            placeholder="Anti Ping Roles",
            row=1,
            min_values=1,
            max_values=10,
            default_values=[discord.Object(id=role) for role in anti_ping_roles] if anti_ping_roles else []
        )
        self.anti_ping_role_select.callback = self.anti_ping_roles
        self.add_item(self.anti_ping_role_select)

        self.bypass_anti_ping_role_select = discord.ui.RoleSelect(
            placeholder="Bypass Anti Ping Roles",
            row=2,
            min_values=1,
            max_values=10,
            default_values=[discord.Object(id=role) for role in bypass_anti_ping_roles] if bypass_anti_ping_roles else []
        )
        self.bypass_anti_ping_role_select.callback = self.bypass_anti_ping_roles
        self.add_item(self.bypass_anti_ping_role_select)

    async def anti_ping_enable_callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        set_anti_ping_option(guild_id, not get_anti_ping_option(guild_id))
        embed = discord.Embed(description="Anti Ping Option saved.", color=0x2F3136)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def anti_ping_roles(self, interaction: discord.Interaction):
        response = [role.id for role in self.anti_ping_role_select.values]
        guild_id = interaction.guild.id
        save_anti_ping_roles(guild_id, response)
        embed = discord.Embed(description="Anti Ping Roles saved.", color=0x2F3136)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def bypass_anti_ping_roles(self, interaction: discord.Interaction):
        response = [role.id for role in self.bypass_anti_ping_role_select.values]
        guild_id = interaction.guild.id
        save_anti_ping_bypass_roles(guild_id, response)
        embed = discord.Embed(description="Bypass Anti Ping Roles saved.", color=0x2F3136)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
class PromotionDemotionLogs(View):
    def __init__(self,promotion_channel_id = None,infraction_channel_id = None):
        super().__init__()
        
        self.promotion_channel = discord.ui.ChannelSelect(
            placeholder="Select Promotion Channel",
            row=0,
            default_values = [discord.Object(id=promotion_channel_id)] if promotion_channel_id else []
        )
        self.promotion_channel.callback = self.promotion_channel_callback
        self.add_item(self.promotion_channel)

        self.infraction_channel = discord.ui.ChannelSelect(
            placeholder="Select Infraction Channel",
            row=1,
            default_values= [discord.Object(id=infraction_channel_id)] if infraction_channel_id else []
        )
        self.infraction_channel.callback = self.infraction_channel_callback
        self.add_item(self.infraction_channel)

    async def promotion_channel_callback(self, interaction: discord.Interaction):
        response = self.promotion_channel.values[0].id if self.promotion_channel.values else None
        guild_id = interaction.guild.id
        save_promotion_channel(guild_id, response)
        embed = discord.Embed(description="Promotion Channel saved.", color=0x2F3136)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def infraction_channel_callback(self, interaction: discord.Interaction):
        response = self.infraction_channel.values[0].id if self.infraction_channel.values else None
        guild_id = interaction.guild.id
        save_infraction_channel(guild_id, response)
        embed = discord.Embed(description="Infraction Channel saved.", color=0x2F3136)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
class ApplicationAndModLogView(View):
    def __init__(self,application_channel_id=None,mod_log_channel_id=None):
        super().__init__()
        self.application_channel = discord.ui.ChannelSelect(
            placeholder="Select Application Channel",
            row=0,
            default_values = [discord.Object(id=application_channel_id)] if application_channel_id else []
        )
        self.application_channel.callback = self.application_channel_callback
        self.add_item(self.application_channel)

        self.mod_log_channel = discord.ui.ChannelSelect(
            placeholder="Select Mod Log Channel",
            row=1,
            default_values= [discord.Object(id=mod_log_channel_id)] if mod_log_channel_id else []
        )
        self.mod_log_channel.callback = self.mod_log_channel_callback
        self.add_item(self.mod_log_channel)

    async def application_channel_callback(self, interaction: discord.Interaction):
        response = self.application_channel.values[0].id if self.application_channel.values else None
        guild_id = interaction.guild.id
        save_application_channel(guild_id, response)
        embed = discord.Embed(description="Application Channel saved.", color=0x2F3136)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def mod_log_channel_callback(self, interaction: discord.Interaction):
        response = self.mod_log_channel.values[0].id if self.mod_log_channel.values else None
        guild_id = interaction.guild.id
        save_mod_log_channel(guild_id, response)
        embed = discord.Embed(description="Mod Log Channel saved.", color=0x2F3136)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class MessageQuotaAndPrefixView(View):
    def __init__(self, message_quota=None, prefix=None):
        super().__init__()

        self.message_quota = discord.ui.Button(
            label="Message Quota",
            style=discord.ButtonStyle.primary,
            row=0
        )
        self.message_quota.callback = self.message_quota_callback
        self.add_item(self.message_quota)

        self.prefix = discord.ui.Button(
            label="Prefix",
            style=discord.ButtonStyle.primary,
            row=1
        )
        self.prefix.callback = self.prefix_callback
        self.add_item(self.prefix)

    async def message_quota_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(MessageQuota())

    async def prefix_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(Prefix())