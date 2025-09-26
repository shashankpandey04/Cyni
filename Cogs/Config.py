# import discord
# from discord.ext import commands
# from Views.Config import StaffToolsView, ServerManagementView, GameIntegrationView
# from utils.pagination import Pagination
# from cyni import is_management, premium_check
# from utils.constants import BLANK_COLOR, RED_COLOR
# from utils.utils import log_command_usage
# class Config(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot

#     @commands.hybrid_command(
#         name="config",
#         aliases=["settings"],
#         extras={
#             "category": "Settings"
#         }
#     )
#     @commands.guild_only()
#     @is_management()
#     @premium_check()
#     async def config(self, ctx):
#         """
#         Configure your server settings.
#         """
#         if not ctx.author or not hasattr(ctx.author, 'id'):
#             return await ctx.send(
#                 embed=discord.Embed(
#                     title="Error",
#                     description="Unable to identify the command user.",
#                     color=RED_COLOR
#                 )
#             )
            
#         try:
#             if isinstance(ctx,commands.Context):
#                 await log_command_usage(self.bot,ctx.guild,ctx.author,"Config")
#         except:
#             pass
#         try:
#             sett = await self.bot.settings.find_by_id(ctx.guild.id)
#             if not sett:
#                 sett = {}
#         except KeyError:
#             sett = {}
#         try:
            
#             prefix = sett.get('customization', {})
#             if self.bot.is_premium:
#                 prefix = prefix.get('premium_prefix', '?')
#             else:
#                 prefix = prefix.get('prefix', '?')

#             landing_embed = discord.Embed(
#                 title="Configuration Menu",
#                 description=(
#                     "This landing page provides an overview of the available configuration modules.\n"
#                     "> **Staff Tools**\n"
#                     f"> - {self.bot.emoji.get('antiping')} Anti-Ping Module: {'**Enabled**' if sett.get('anti_ping_module', {}).get('enabled', False) else '**Disabled**'}\n"
#                     f"> - {self.bot.emoji.get('moderation')} Moderation Module: {'**Enabled**' if sett.get('moderation_module', {}).get('enabled', False) else '**Disabled**'}\n"
#                     f"> - 📝 Staff Infraction Module: {'**Enabled**' if sett.get('staff_management', {}).get('enabled', False) else '**Disabled**'}\n"
#                     f"> - {self.bot.emoji.get('loa')} LOA Module: {'**Enabled**' if sett.get('leave_of_absence', {}).get('enabled', False) else '**Disabled**'}\n\n"
#                     "> **Server Management**\n"
#                     f"> - {self.bot.emoji.get('utility')} Prefix: {'`' + prefix + '`'}\n"
#                     f"> - {self.bot.emoji.get('partnership')} Partnership Module: {'**Enabled**' if sett.get('partnership_module', {}).get('enabled', False) else '**Disabled**'}\n\n"
#                     "> **Game Integrations**\n"
#                     f"> - {self.bot.emoji.get('roblox')} Roblox Management\n"
#                     f">  - Staff Roles: {'**Configured**' if sett.get('roblox', {}).get('staff_roles', False) else '**Not Configured**'}\n"
#                     f">  - Shift Module: {'**Configured**' if sett.get('roblox', {}).get('shift_module',{}).get('channel', False) else '**Not Configured**'}\n"
#                     f">  - Punishment Module: {'**Configured**' if sett.get('roblox', {}).get('punishments',{}).get('enabled', False) else '**Not Configured**'}\n"
#                     f"> - {self.bot.emoji.get('prc')} ER:LC Automations\n"
#                     f">  - Kill Logs: {'**Configured**' if sett.get('erlc', {}).get('kill_logs_channel', False) else '**Not Configured**'}\n"
#                     f">  - Join Logs: {'**Configured**' if sett.get('erlc', {}).get('join_logs_channel', False) else '**Not Configured**'}\n"
#                     f">  - Discord Checks: {'**Enabled**' if sett.get('erlc', {}).get('discord_check_log_channel', False) else '**Disabled**'}\n"
#                     f">  - Auto Kick/Ban Log: {'**Configured**' if sett.get('erlc', {}).get('kick_ban_log_channel', False) else '**Not Configured**'}\n"
#                     f">  - Remote Command Logs: {'**Configured**' if sett.get('erlc', {}).get('command_log_channel', False) else '**Not Configured**'}\n\n"
#                 ),
#                 color=BLANK_COLOR
#             )

#             landing_embed = discord.Embed(
#                 title="Configuration Menu",
#                 description=(
#                     "This landing page provides an overview of the available configuration modules.\n"
#                     "> Thank you for choosing CYNI to manage your community! Use the buttons below to navigate through different configuration modules and customize your server settings.\n\n"
#                     "To view overall configuration of your server please use the dropdown available below."
#                 ),
#                 color=BLANK_COLOR
#             )

#             embed_staff = discord.Embed(
#                 title="Staff Tools",
#                 description="Modules designed to help your staff moderate, manage infractions, and track activity.",
#                 color=BLANK_COLOR
#             ).add_field(
#                 name=f"{self.bot.emoji.get('antiping')} Anti-Ping Module",
#                 value="> Configure anti-ping settings to prevent users from pinging specific roles.",
#                 inline=False
#             ).add_field(
#                 name=f"{self.bot.emoji.get('moderation')} Moderation Module",
#                 value="> Configure roles who can access moderation commands & dashboard.",
#                 inline=False
#             ).add_field(
#                 name="📝 Staff Infraction Module",
#                 value="> Configure staff infraction settings to track and manage staff behavior.",
#                 inline=False
#             ).add_field(
#                 name=f"{self.bot.emoji.get('loa')} LOA Module",
#                 value="> Configure LOA (Leave of Absence) settings to manage staff absences effectively.",
#                 inline=False
#             )

#             embed_management = discord.Embed(
#                 title="Server Management",
#                 description="Modules designed to streamline administration and manage your community.",
#                 color=BLANK_COLOR
#             ).add_field(
#                 name=f"{self.bot.emoji.get('utility')} Server Utility Module",
#                 value="> Configure server utility settings for effective server management.",
#                 inline=False
#             ).add_field(
#                 name=f"{self.bot.emoji.get('partnership')} Partnership Module",
#                 value="> Configure partnership settings to manage partnerships effectively.",
#                 inline=False
#             )

#             embed_game = discord.Embed(
#                 title="Game Integrations",
#                 description="Modules that connect CYNI with Roblox and ER:LC for community/game management.",
#                 color=BLANK_COLOR
#             ).add_field(
#                 name=f"{self.bot.emoji.get('roblox')} Roblox Management",
#                 value="> Configure Roblox Staff Roles, Punishments & Shifts for your community.",
#                 inline=False
#             ).add_field(
#                 name=f"{self.bot.emoji.get('prc')} ER:LC Automations",
#                 value="> Configure ER:LC (Emergency Response: Liberty County) automations to manage your ER:LC community effectively.",
#                 inline=False
#             )

#             all_embed = [landing_embed, embed_staff, embed_management, embed_game]
#             views = [
#                 discord.ui.View(),
#                 StaffToolsView(self.bot, ctx),
#                 ServerManagementView(self.bot, ctx),
#                 GameIntegrationView(self.bot, ctx)
#             ]
#             view = Pagination(self.bot, ctx.author.id, all_embed, views)
#             await ctx.send(embed=landing_embed, view=view)

#         except Exception as e:
#             return await ctx.send(
#                 embed=discord.Embed(
#                     title="Something went wrong",
#                     description=f"```{e}```",
#                     color=RED_COLOR
#                 )
#             )

# async def setup(bot):
#     await bot.add_cog(Config(bot))

import discord
from discord.ext import commands
from menu import (
    BasicConfig, AntiPingView, ModerationModule, 
    StaffInfraction, ServerManagement, PartnershipModule,
    LOAConfig
)
from Views.RobloxManagement import RobloxManagement
from utils.pagination import Pagination
from cyni import is_management, premium_check
from utils.constants import BLANK_COLOR, RED_COLOR
from utils.utils import log_command_usage
class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="config",
        aliases=["settings"],
        extras={
            "category": "Settings"
        }
    )
    @commands.guild_only()
    @is_management()
    @premium_check()
    async def config(self, ctx):
        """
        Configure your server settings.
        """
        if not ctx.author or not hasattr(ctx.author, 'id'):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Unable to identify the command user.",
                    color=RED_COLOR
                )
            )
            
        try:
            if isinstance(ctx,commands.Context):
                await log_command_usage(self.bot,ctx.guild,ctx.author,"Config")
        except:
            pass
        try:
            sett = await self.bot.settings.find_by_id(ctx.guild.id)
            if not sett:
                sett = {}
        except KeyError:
            sett = {}
        try:
            embed1 = discord.Embed(
                title="Basic Configuration",
                description="> This is the basic configuration for your server. But what does it do?\n"
                            "> The basic configuration allows you to set the following settings:\n"
                            "> These settings are crucial for the bot to function properly.\n\n"
                            f"{self.bot.emoji.get('arrow')} **Staff Role**\n"
                            "- The role that is considered as discord staff and can use Moderation commands and other staff commands.\n\n"
                            f"{self.bot.emoji.get('arrow')} **Management Role**\n"
                            "- The role that is considered as discord management and can use Management commands link Staff Infraction, Application Results, Ban Appeal Results, etc.\n\n"
                            f"{self.bot.emoji.get('arrow')} **Prefix**\n"
                            "- The prefix that the bot will use for commands."
                            ,
                color=BLANK_COLOR
            )

            embed2 = discord.Embed(
                title="Anti-Ping Module",
                description="> What is Anti-Ping? Anti-Ping prevents users from pinging specific roles.\n"
                            "> To configure Anti-Ping, you need to set the following settings:\n\n"
                            f"{self.bot.emoji.get('arrow')} **Anti-Ping Roles**\n"
                            "- These roles clarify the individuals who are affected by Anti-Ping, and are classed as important individuals to Cyni. An individual who pings someone with these affected roles, will activate Anti-Ping.\n\n"
                            f"{self.bot.emoji.get('arrow')} **Bypass Roles**\n"
                            "-  An individual who holds one of these roles will not be able to trigger Anti-Ping filters, and will be able to ping any individual within the Affected Roles list without Cyni intervening."
                            ,
                color=BLANK_COLOR
            )

            embed3 = discord.Embed(
                title="Moderation Module",
                description="> What is Moderation module? The moderation module allows you to configure the following settings:\n\n"
                            f"{self.bot.emoji.get('arrow')} **Moderation Log Channel**\n"
                            "- The channel where moderation logs will be sent.\n"
                            f"{self.bot.emoji.get('arrow')} **Ban Appeal Channel**\n"
                            "- The channel where ban appeals will be sent.\n"
                            f"{self.bot.emoji.get('arrow')} **Audit Log Channel**\n"
                            "- The channel where audit logs will be sent like message edits, message deletes, etc.",
                color=BLANK_COLOR
            )

            embed4 = discord.Embed(
                title="Staff Infraction Module",
                description="> What is Staff Management module? The staff management module allows you to configure the following settings:\n"
                            f"{self.bot.emoji.get('arrow')} **Promotion Log Channel**\n"
                            "- The channel where staff promotions will be sent.\n\n"
                            f"{self.bot.emoji.get('arrow')} **Demotion Log Channel**\n"
                            "- The channel where staff demotions will be sent.\n\n"
                            f"{self.bot.emoji.get('arrow')} **Warning Log Channel**\n"
                            "- The channel where staff warnings will be sent like staff strikes and warnings."
                            ,
                color=BLANK_COLOR
            )

            embed5 = discord.Embed(
                title="Server Management Module",
                description="> What is Server Management module? The server management module allows you to configure the following settings:\n\n"
                            f"{self.bot.emoji.get('arrow')} **Application Results Channel**\n"
                            "- The channel where application results will be sent.\n\n"
                            f"{self.bot.emoji.get('arrow')} **Cyni Logging Channel**\n"
                            "- The channel where Cyni command & config change logs will be sent."
                            f"{self.bot.emoji.get('arrow')} **Suggestion Channel**\n"
                            "- The channel where suggestions will be sent and users can vote on them.",
                color=BLANK_COLOR
            )

            embed6 = discord.Embed(
                title="Partnership Module",
                description="> **What is Partnership module?**\n The partnership module allows you to configure the following settings:\n\n"
                            f"{self.bot.emoji.get('arrow')} **Partnership Module Enabled**\n"
                            "- Enable or disable the partnership module.\n\n"
                            f"{self.bot.emoji.get('arrow')} **Partnership Channel**\n"
                            "- The channel where partnership logs will be sent.\n\n"
                            f"{self.bot.emoji.get('arrow')} **Partner Role**\n"
                            "- The role that is considered as a partner and automatically given when a partnership is logged."
                            ,
                color=BLANK_COLOR
            )

            embed7 = discord.Embed(
                title="LOA Module",
                description=(
                    "> **Enabled**\n"
                    "This setting allows you to enable or disable the LOA module. If the LOA module is disabled, users will not be able to request LOAs.\n\n"
                    "> **LOA Role**\n"
                    "This role will be given to users when their LOA request is accepted and removed when it expires.\n\n"
                    "> **LOA Channel**\n"
                    "This channel is where LOA requests will be sent for staff to review and accept or decline."
                )
            )

            embed_8 = discord.Embed(
                title="Roblox Management",
                description=(
                    "> **Staff Configuration**\n"
                    "This setting allows you to configure the staff & management roles and permissions to access Roblox-related commands.\n\n"
                    "> **Shifts Configuration**\n"
                    "This setting allows you to configure the shifts and scheduling for your Roblox staff.\n\n"
                    "> **Punishments Configuration**\n"
                    "This setting allows you to configure the punishments for your Roblox staff.\n\n"
                )
            )

            all_embed = [embed1, embed2, embed3, embed4, embed5, embed6, embed7, embed_8]
            views = [
                BasicConfig(self.bot, sett, ctx.author.id), 
                AntiPingView(self.bot, sett, ctx.author.id), 
                ModerationModule(bot=self.bot,setting=sett,user_id=ctx.author.id),
                StaffInfraction(bot=self.bot,setting=sett,user_id=ctx.author.id),
                ServerManagement(bot=self.bot,setting=sett,user_id=ctx.author.id),
                PartnershipModule(bot=self.bot,setting=sett,user_id=ctx.author.id),
                LOAConfig(bot=self.bot,setting=sett,user_id=ctx.author.id),
                RobloxManagement(self.bot, ctx, sett)
            ]
            view = Pagination(self.bot, ctx.author.id, all_embed, views)
            await ctx.send(embed=embed1, view=view)

        except Exception as e:
            return await ctx.send(
                embed=discord.Embed(
                    title="Something went wrong",
                    description=f"```{e}```",
                    color=RED_COLOR
                )
            )

async def setup(bot):
    await bot.add_cog(Config(bot))