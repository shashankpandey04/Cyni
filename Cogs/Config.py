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
from Views.Config import StaffToolsView, ServerManagementView, GameIntegrationView
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
            
            prefix = sett.get('customization', {})
            if self.bot.is_premium:
                prefix = prefix.get('premium_prefix', '?')
            else:
                prefix = prefix.get('prefix', '?')

            landing_embed = discord.Embed(
                title="Configuration Menu",
                description=(
                    "This landing page provides an overview of the available configuration modules.\n"
                    "> **Staff Tools**\n"
                    f"> - {self.bot.emoji.get('antiping')} Anti-Ping Module: {'**Enabled**' if sett.get('anti_ping_module', {}).get('enabled', False) else '**Disabled**'}\n"
                    f"> - {self.bot.emoji.get('moderation')} Moderation Module: {'**Enabled**' if sett.get('moderation_module', {}).get('enabled', False) else '**Disabled**'}\n"
                    f"> - 📝 Staff Infraction Module: {'**Enabled**' if sett.get('staff_management', {}).get('enabled', False) else '**Disabled**'}\n"
                    f"> - {self.bot.emoji.get('loa')} LOA Module: {'**Enabled**' if sett.get('leave_of_absence', {}).get('enabled', False) else '**Disabled**'}\n\n"
                    "> **Server Management**\n"
                    f"> - {self.bot.emoji.get('utility')} Prefix: {'`' + prefix + '`'}\n"
                    f"> - {self.bot.emoji.get('partnership')} Partnership Module: {'**Enabled**' if sett.get('partnership_module', {}).get('enabled', False) else '**Disabled**'}\n\n"
                    "> **Game Integrations**\n"
                    f"> - {self.bot.emoji.get('roblox')} Roblox Management\n"
                    f">  - Staff Roles: {'**Configured**' if sett.get('roblox', {}).get('staff_roles', False) else '**Not Configured**'}\n"
                    f">  - Shift Module: {'**Configured**' if sett.get('roblox', {}).get('shift_module',{}).get('channel', False) else '**Not Configured**'}\n"
                    f">  - Punishment Module: {'**Configured**' if sett.get('roblox', {}).get('punishments',{}).get('enabled', False) else '**Not Configured**'}\n"
                    f"> - {self.bot.emoji.get('prc')} ER:LC Automations\n"
                    f">  - Kill Logs: {'**Configured**' if sett.get('erlc', {}).get('kill_logs_channel', False) else '**Not Configured**'}\n"
                    f">  - Join Logs: {'**Configured**' if sett.get('erlc', {}).get('join_logs_channel', False) else '**Not Configured**'}\n"
                    f">  - Discord Checks: {'**Enabled**' if sett.get('erlc', {}).get('discord_check_log_channel', False) else '**Disabled**'}\n"
                    f">  - Auto Kick/Ban Log: {'**Configured**' if sett.get('erlc', {}).get('kick_ban_log_channel', False) else '**Not Configured**'}\n"
                    f">  - Remote Command Logs: {'**Configured**' if sett.get('erlc', {}).get('command_log_channel', False) else '**Not Configured**'}\n\n"
                ),
                color=BLANK_COLOR
            )

            embed_staff = discord.Embed(
                title="Staff Tools",
                description="Modules designed to help your staff moderate, manage infractions, and track activity.",
                color=BLANK_COLOR
            ).add_field(
                name=f"{self.bot.emoji.get('antiping')} Anti-Ping Module",
                value="> Configure anti-ping settings to prevent users from pinging specific roles.",
                inline=False
            ).add_field(
                name=f"{self.bot.emoji.get('moderation')} Moderation Module",
                value="> Configure roles who can access moderation commands & dashboard.",
                inline=False
            ).add_field(
                name="📝 Staff Infraction Module",
                value="> Configure staff infraction settings to track and manage staff behavior.",
                inline=False
            ).add_field(
                name=f"{self.bot.emoji.get('loa')} LOA Module",
                value="> Configure LOA (Leave of Absence) settings to manage staff absences effectively.",
                inline=False
            )

            embed_management = discord.Embed(
                title="Server Management",
                description="Modules designed to streamline administration and manage your community.",
                color=BLANK_COLOR
            ).add_field(
                name=f"{self.bot.emoji.get('utility')} Server Utility Module",
                value="> Configure server utility settings for effective server management.",
                inline=False
            ).add_field(
                name=f"{self.bot.emoji.get('partnership')} Partnership Module",
                value="> Configure partnership settings to manage partnerships effectively.",
                inline=False
            )

            embed_game = discord.Embed(
                title="Game Integrations",
                description="Modules that connect CYNI with Roblox and ER:LC for community/game management.",
                color=BLANK_COLOR
            ).add_field(
                name=f"{self.bot.emoji.get('roblox')} Roblox Management",
                value="> Configure Roblox Staff Roles, Punishments & Shifts for your community.",
                inline=False
            ).add_field(
                name=f"{self.bot.emoji.get('prc')} ER:LC Automations",
                value="> Configure ER:LC (Emergency Response: Liberty County) automations to manage your ER:LC community effectively.",
                inline=False
            )

            all_embed = [landing_embed, embed_staff, embed_management, embed_game]
            views = [
                discord.ui.View(),  # Empty view for landing page
                StaffToolsView(self.bot, ctx),
                ServerManagementView(self.bot, ctx),
                GameIntegrationView(self.bot, ctx)
            ]
            view = Pagination(self.bot, ctx.author.id, all_embed, views)
            await ctx.send(embed=landing_embed, view=view)

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