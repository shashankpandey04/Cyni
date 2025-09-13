import discord
from discord import app_commands
from discord.ext import commands

from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR, YELLOW_COLOR
from cyni import is_staff_or_management,is_management, premium_check
from utils.Schema import warning
from utils.utils import log_command_usage
from datetime import timedelta, datetime
from utils.utils import parse_duration
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="warn",
        aliases=["w"],
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        member="Member to warn",
        reason="Reason for the warning"
    )
    @premium_check()
    async def warn(self, ctx, member: discord.Member, *, reason: str = None):
        """
        Warn a user.
        """
        if reason is None:
            return await ctx.send(
                embed=discord.Embed(
                    description="Please provide a reason for the warning.",
                    color=RED_COLOR
                )
            )
        if isinstance(ctx, commands.Context):
            await log_command_usage(self.bot, ctx.guild, ctx.author, f"Warn {member}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed=discord.Embed(
                    description="No settings found.\nPlease set up the bot using the `config` command.",
                    color=RED_COLOR
                )
            )
        module_enabled = settings.get("moderation_module", {}).get("enabled", False)
        if not module_enabled:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"{self.bot.emoji.get('moderation')} Moderation module is not enabled.",
                    color=RED_COLOR
                )
            )
        if member == ctx.author:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"{self.bot.emoji.get('moderation')} You cannot warn yourself.",
                    color=RED_COLOR
                )
            )

        total_warnings = await self.bot.warnings.find(
            {
                'guild_id': ctx.guild.id,
            }
        )
        total_warnings = len(total_warnings)

        doc = {
            'guild_id': ctx.guild.id,
            'user_id': member.id,
            'reason': reason,
            'moderator_id': ctx.author.id,
            'timestamp': datetime.now().timestamp(),
            'case_id': total_warnings + 1,
            'active': True,
            'void': False,
            'type': 'warn',
        }

        await self.bot.warnings.insert_one(doc)
        await ctx.send(
            embed=discord.Embed(
                description=f"{self.bot.emoji.get('moderation')}{member.mention} has been warned for `{reason}`.\nCase ID: {total_warnings + 1}",
                color=GREEN_COLOR
            )
        )
        await member.send(
            embed=discord.Embed(
                description=f"You have been warned in **{ctx.guild.name}**\n\n**Case ID:** {total_warnings + 1}\n> **Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                color=RED_COLOR
            )
        )
        log_channel = ctx.guild.get_channel(settings.get("moderation_module", {}).get("mod_log_channel", 0))
        if log_channel != 0:
            await log_channel.send(
                embed=discord.Embed(
                    title=f"Case {total_warnings + 1} | Warn",
                    description=f"**User:** {member.mention}\n> **Moderator:** {ctx.author.mention}\n> **Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                    color=GREEN_COLOR
                )
            )
        else:
            embed = discord.Embed(
                description=f"{self.bot.emoji.get('moderation')} Moderation log channel not found. Please set up the bot using the `config` command.",
                color=RED_COLOR
            )
            await ctx.channel.send(
                embed=embed
            )

    @commands.hybrid_command(
        name="warnings",
        aliases=["warns", "modlogs"],
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        member="Member to view warnings for"
    )
    @premium_check()
    async def warnings(self, ctx, member: discord.Member):
        """
        Get the warnings for a user.
        """
        try:
            settings = await self.bot.settings.find_by_id(ctx.guild.id)
            if not settings:
                return await ctx.send(
                    embed = discord.Embed(
                        description = "No settings found.\nPlease set up the bot using the `config` command.",
                        color = RED_COLOR
                    )
                )
            module_enabled = settings.get("moderation_module",{}).get("enabled",False)
            if not module_enabled:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{self.bot.emoji.get('moderation')} Moderation module is not enabled.",
                        color = RED_COLOR
                    )
                )
            user_warnings = await self.bot.warnings.find(
                {
                    'guild_id': ctx.guild.id,
                    'user_id': member.id,
                }
            )
            if not user_warnings:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{self.bot.emoji.get('moderation')} {member.mention} has no warnings.",
                        color = GREEN_COLOR
                    )
                )
            embed = discord.Embed(
                title = f"{member.name}'s Warnings",
                description=" ",
                color = RED_COLOR
            )
            for warning in user_warnings:
                if warning['type'] == 'mute':
                    try:
                        duration = warning['duration']
                    except KeyError:
                        duration = "No duration specified"
                    embed.description += (
                        f"**Case ID:** {warning['case_id']}\n"
                        f"> **Reason:** {warning['reason']}\n"
                        f"> **Moderator:** <@{warning['moderator_id']}>\n"
                        f"> **Type:** {warning['type']}\n"
                        f"> **Timestamp:** <t:{int(warning['timestamp'])}:R>\n"
                        f"> **Duration:** {duration}\n"
                        f"> **Status:** {'Active' if warning['active'] else 'Voided'}\n\n"
                    )
                else:
                    embed.description += (
                        f"**Case ID:** {warning['case_id']}\n"
                        f"> **Reason:** {warning['reason']}\n"
                        f"> **Moderator:** <@{warning['moderator_id']}>\n"
                        f"> **Type:** {warning['type']}\n"
                        f"> **Timestamp:** <t:{int(warning['timestamp'])}:R>\n"
                        f"> **Status:** {'Active' if warning['active'] else 'Voided'}\n\n"
                    )

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(
                embed = discord.Embed(
                    description = f"An error occurred while fetching warnings for {member.mention}: {str(e)}",
                    color = RED_COLOR
                )
            )

    @commands.hybrid_command(
        name="void",
        aliases=["v"],
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        case="Case ID of the warning to void"
    )
    @premium_check()
    async def delwarn(self, ctx, case: int):
        """
        Delete a warning for a user.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Cleared warning {case}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        module_enabled = settings.get("moderation_module",{}).get("enabled",False)
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{self.bot.emoji.get('moderation')} Moderation module is not enabled.",
                    color = RED_COLOR
                )
            )
        user_warning = await self.bot.warnings.find_one(
            {
                'guild_id': ctx.guild.id,
                'case_id': case,
            }
        )
        if not user_warning:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{self.bot.emoji.get('moderation')} Warning with case ID {case} not found.",
                    color = GREEN_COLOR
                )
            )
        user_warning['active'] = False
        user_warning['void'] = True
        await self.bot.warnings.update_by_id(user_warning)
        await ctx.send(
            embed = discord.Embed(
                description = f"{self.bot.emoji.get('moderation')} Warning with case ID {case} has been voided.",
                color = GREEN_COLOR
            )
        )
        mod_log_channel = ctx.guild.get_channel(settings.get("moderation_module",{}).get("mod_log_channel",0))
        if mod_log_channel != 0:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = f"Case ID: {case} | Warning Voided",
                    description = f"**User ID:** <@{user_warning['user_id']}>\n> **Moderator:** {ctx.author.mention}\n> **Reason:** Warning voided\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                    color = GREEN_COLOR
                )
            )
        else:
            await ctx.channel.send(
                embed=discord.Embed(
                    description = f"{self.bot.emoji.get('moderation')} Moderation log channel not found. Please set up the bot using the `config` command.",
                    color = RED_COLOR
                )
            )

    @commands.hybrid_command(
        name='case',
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        case="Case ID of the warning to view"
    )
    @premium_check()
    async def case(self, ctx, case: int):
        """
        Get the details of a case.
        """
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed=discord.Embed(
                    description="No settings found.\nPlease set up the bot using the `config` command.",
                    color=RED_COLOR
                )
            )
        
        module_enabled = settings.get("moderation_module", {}).get("enabled", False)
        if not module_enabled:
            return await ctx.send(
                embed=discord.Embed(
                    description= f"{self.bot.emoji.get('moderation')} Moderation module is not enabled.",
                    color=RED_COLOR
                )
            )
        
        user_warning = await self.bot.warnings.find_one(
            {
                'guild_id': ctx.guild.id,
                'case_id': case,
            }
        )
        
        if not user_warning:
            return await ctx.send(
                embed=discord.Embed(
                    description= f"{self.bot.emoji.get('moderation')} Warning with case ID {case} not found.",
                    color=GREEN_COLOR
                )
            )
        
        embed = discord.Embed(
            title= f"{self.bot.emoji.get('moderation')} | Case ID: {case}",
            description=f"**User:** <@{user_warning['user_id']}>\n> **Reason:** {user_warning['reason']}\n> **Moderator:** <@{user_warning['moderator_id']}>\n> **Type:** {user_warning['type']}\n> **Timestamp:** <t:{int(user_warning['timestamp'])}:R>\n> **Status:** {'Active' if user_warning['active'] else 'Void'}",
            color=YELLOW_COLOR
        )
        
        await ctx.send(embed=embed)


    @commands.hybrid_command(
        name="kick",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        member="Member to kick",
        reason="Reason for the kick"
    )
    @premium_check()
    async def kick(self, ctx, member: discord.Member, *, reason: str):
        """
        Kick a user.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Kick {member}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        module_enabled = settings.get("moderation_module",{}).get("enabled",False)
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = RED_COLOR
                )
            )
        if ctx.author.top_role.position <= member.top_role.position:
            return await ctx.send(
                embed = discord.Embed(
                    title="Looks like you can't do that",
                    description="You can't kick this user because they have a higher role than you.",
                    color=RED_COLOR
                )
            )

        total_warnings = await self.bot.warnings.find(
            {
                'guild_id': ctx.guild.id,
            }
        )
        total_warnings = len(total_warnings)
        
        doc = {
            'guild_id': ctx.guild.id,
            'user_id': member.id,
            'reason': reason,
            'moderator_id': ctx.author.id,
            'timestamp': datetime.now().timestamp(),
            'case_id': total_warnings + 1,
            'active': True,
            'void': False,
            'type': 'kick',
        }
        await self.bot.warnings.insert_one(doc)

        await member.kick(reason=reason)
        await ctx.send(
            embed = discord.Embed(
                title=f"Case ID: {total_warnings + 1}",
                description = f"{member.mention} has been kicked for `{reason}`.",
                color = GREEN_COLOR
            )
        )
        mod_log_channel = ctx.guild.get_channel(settings.get("moderation_module",{}).get("mod_log_channel",0))
        if mod_log_channel != 0:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = f"Case ID: {total_warnings + 1} | User Kicked",
                    description = f"**User ID:** {member.mention}\n> **Moderator:** {ctx.author.mention}\n> **Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                embed=discord.Embed(
                    title="Moderation log channel not found",
                    description="Moderation log channel not found. Please set up the bot using the `config` command.",
                    color=discord.Color.red()
                )
            )

    @commands.hybrid_command(
        name="ban",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        member="Member to ban",
        reason="Reason for the ban"
    )
    @premium_check()
    async def ban(self, ctx, member: discord.Member, *, reason: str):
        """
        Ban a user.
        """
        if not ctx.guild.me.guild_permissions.ban_members:
            return await ctx.send(
                embed = discord.Embed(
                    description = "I do not have permission to ban members.",
                    color = discord.Color.red()
                )
            )
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Ban {member}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        module_enabled = settings.get("moderation_module",{}).get("enabled",False)
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"Moderation module is not enabled.\nPlease set up the bot using the `/config` command.",
                    color = discord.Color.red()
                )
            )
        if ctx.author.top_role.position <= member.top_role.position:
            return await ctx.send(
                embed = discord.Embed(
                    title="Looks like you can't do that",
                    description="You can't ban this user because they have a higher role than you.",
                    color=RED_COLOR
                )
            )
        await member.ban(reason=reason)
        
        total_warnings = await self.bot.warnings.find(
            {
                'guild_id': ctx.guild.id,
            }
        )
        total_warnings = len(total_warnings)

        doc = {
            'guild_id': ctx.guild.id,
            'user_id': member.id,
            'reason': reason,
            'moderator_id': ctx.author.id,
            'timestamp': datetime.now().timestamp(),
            'case_id': total_warnings + 1,
            'active': True,
            'void': False,
            'type': 'ban',
        }
        await self.bot.warnings.insert_one(doc)

        await ctx.send(
            embed = discord.Embed(
                title=f"Case ID: {total_warnings + 1}",
                description = f"{member.mention} has been banned for `{reason}`.",
                color = discord.Color.green()
            )
        )

        try:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Appeal",
                url=f"https://cyni.quprdigital.tk/banappeal/{ctx.guild.id}"
            ))
            await member.send(
                embed = discord.Embed(
                    title = f"You have been banned in {ctx.guild.name}",
                    description = f"**Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                    color = RED_COLOR
                ),
                view=view
            )
        except discord.Forbidden:
            pass
        mod_log_channel = ctx.guild.get_channel(settings.get("moderation_module",{}).get("mod_log_channel",0))
        if mod_log_channel != 0:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "Case ID: {total_warnings + 1} | User Banned",
                    description = f"**User ID:** {member.mention}\n> **Moderator:** {ctx.author.mention}\n> **Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                embed=discord.Embed(
                    description = "Moderation log channel not found. Please set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )

    @commands.hybrid_command(
        name="unban",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        userid="User ID to unban",
        reason="Reason for the unban"
    )
    @premium_check()
    async def unban(self, ctx, userid:str, *, reason: str = "No reason provided."):
        """
        Unban a user.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Unban {userid}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        module_enabled = settings.get("moderation_module",{}).get("enabled",False)
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        userid = int(userid)
        banned_users = await ctx.guild.bans()
        if not any(ban.user.id == userid for ban in banned_users):
            return await ctx.send(
                embed = discord.Embed(
                    description = "User is not banned.",
                    color = discord.Color.red()
                )
            )
        member = discord.Object(id=userid)
        await ctx.guild.unban(member, reason=reason)

        total_warnings = await self.bot.warnings.find(
            {
                'guild_id': ctx.guild.id,
            }
        )
        total_warnings = len(total_warnings)

        doc = {
            'guild_id': ctx.guild.id,
            'user_id': userid,
            'reason': reason,
            'moderator_id': ctx.author.id,
            'timestamp': datetime.now().timestamp(),
            'case_id': total_warnings + 1,
            'active': True,
            'void': False,
            'type': 'unban',
        }
        await self.bot.warnings.insert_one(doc)

        await ctx.send(
            embed = discord.Embed(
                title=f"Case ID: {total_warnings + 1}",
                description = f"{member.mention} has been unbanned for `{reason}`.",
                color = GREEN_COLOR
            )
        )
        mod_log_channel = ctx.guild.get_channel(settings.get("moderation_module",{}).get("mod_log_channel",0))
        if mod_log_channel != 0:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = f"Case ID: {total_warnings + 1} | User Unbanned",
                    description = f"**User ID:** {member.mention}\n> **Moderator:** {ctx.author.mention}\n> **Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                    color = GREEN_COLOR
                )
            )
        else:
            await ctx.channel.send(
                embed=discord.Embed(
                    description = "Moderation log channel not found. Please set up the bot using the `config` command.",
                    color = RED_COLOR
                )
            )

    @commands.hybrid_command(
        name="mute",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        member="Member to mute",
        time="Duration to mute the user (e.g., 10m, 1h, 1d)",
        reason="Reason for the mute"
    )
    @premium_check()
    async def mute(self, ctx, member: discord.Member, time:str, reason: str):
        """
        Mute a user.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Mute {member} for {time}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        module_enabled = settings.get("moderation_module",{}).get("enabled",False)
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = RED_COLOR
                )
            )
        converted_time = parse_duration(time)
        if not converted_time:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Invalid duration.",
                    color = RED_COLOR
                )
            )
        if ctx.author.top_role.position <= member.top_role.position:
            return await ctx.send(
                embed = discord.Embed(
                    title="Looks like you can't do that",
                    description="You can't mute this user because they have a higher role than you.",
                    color=RED_COLOR
                )
            )
        converted_time = discord.utils.utcnow() + timedelta(seconds=converted_time)
        try:
            await member.edit(timed_out_until=converted_time, reason=reason)
        except Exception as e:
            return await ctx.send(
                embed = discord.Embed(
                    description = "I do not have permission to mute this user.",
                    color = RED_COLOR
                ).add_field(
                    name="Error",
                    value=str(e)
                )
            )
        total_warnings = await self.bot.warnings.find(
            {
                'guild_id': ctx.guild.id,
            }
        )
        total_warnings = len(total_warnings)
        doc = {
            'guild_id': ctx.guild.id,
            'user_id': member.id,
            'reason': reason,
            'moderator_id': ctx.author.id,
            'timestamp': datetime.now().timestamp(),
            'case_id': total_warnings + 1,
            'active': True,
            'void': False,
            'type': 'mute',
            'duration': time,
        }

        await self.bot.warnings.insert_one(doc)
        await ctx.send(
            embed = discord.Embed(
                title=f"Case ID: {total_warnings + 1}",
                description = f"{member.mention} has been muted for `{reason}`.\nTime: {time}",
                color = GREEN_COLOR
            )
        )
        mod_log_channel = ctx.guild.get_channel(settings.get("moderation_module",{}).get("mod_log_channel",0))
        if mod_log_channel != 0:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = f"Case ID: {total_warnings + 1} | User Muted",
                    description = f"**User ID:** {member.mention}\n> **Moderator:** {ctx.author.mention}\n> **Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>\n> **Duration:** {time}",
                    color = RED_COLOR
                )
            )
        else:
            await ctx.channel.send(
                embed=discord.Embed(
                    description = "Moderation log channel not found. Please set up the bot using the `config` command.",
                    color = RED_COLOR
                )
            )
        return await member.send(
            embed = discord.Embed(
                title = f"You have been muted in {ctx.guild.name}",
                description = f"**Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>\n> **Duration:** {time}\n\nIf you believe this is a mistake, please contact the moderation team.",
                color = RED_COLOR
            )
        )

    @commands.hybrid_command(
        name="unmute",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        member="Member to unmute",
        reason="Reason for the unmute"
    )
    @premium_check()
    async def unmute(self, ctx, member: discord.Member, *, reason: str):
        """
        Unmute a user.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Unmute {member}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        module_enabled = settings.get("moderation_module",{}).get("enabled",False)
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        try:
            await member.edit(timed_out_until=None)
        except discord.Forbidden:
            return await ctx.send(
                embed = discord.Embed(
                    description = "I do not have permission to unmute this user.",
                    color = discord.Color.red()
                )
            )
        total_warnings = await self.bot.warnings.find(
            {
                'guild_id': ctx.guild.id,
            }
        )
        total_warnings = len(total_warnings)
        doc = {
            'guild_id': ctx.guild.id,
            'user_id': member.id,
            'reason': reason,
            'moderator_id': ctx.author.id,
            'timestamp': datetime.now().timestamp(),
            'case_id': total_warnings + 1,
            'active': True,
            'void': False,
            'type': 'unmute',
        }
        await self.bot.warnings.insert_one(doc)
        await ctx.send(
            embed = discord.Embed(
                title=f"Case ID: {total_warnings + 1}",
                description = f"{member.mention} has been unmuted for `{reason}`.",
                color = GREEN_COLOR
            )
        )
        mod_log_channel = ctx.guild.get_channel(settings.get("moderation_module",{}).get("mod_log_channel",0))
        if mod_log_channel != 0:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = f"Case ID: {total_warnings + 1} | User Unmuted",
                    description = f"*User ID:** {member.mention}\n> **Moderator:** {ctx.author.mention}\n> **Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                    color = GREEN_COLOR
                )
            )
        else:
            await ctx.channel.send(
                embed=discord.Embed(
                    description = "Moderation log channel not found. Please set up the bot using the `config` command.",
                    color = RED_COLOR
                )
            )


    @commands.hybrid_command(
        name="lock",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        channel="Channel to lock"
    )
    @premium_check()
    async def lock(self, ctx, channel: discord.TextChannel):
        """
        Lock a channel.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Lock {channel}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        try:
            module_enabled = settings["moderation_module"]["enabled"]
        except KeyError:
            module_enabled = False
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        
        for role in ctx.guild.roles:
            if channel.permissions_for(role).send_messages:
                await channel.set_permissions(role, send_messages=False)
        await ctx.send(
            embed = discord.Embed(
                description = f"{channel.mention} has been locked.",
                color = discord.Color.green()
            )
        )
        try:
            mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        except KeyError:
            mod_log_channel = None
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "Channel Locked",
                    description = f"**Channel:** {channel.mention}\n**Moderator:** {ctx.author.mention}",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                "Moderation log channel not found. Please set up the bot using the `config` command."
            )


    @commands.hybrid_command(
        name="unlock",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        channel="Channel to unlock"
    )
    @premium_check()
    async def unlock(self, ctx, channel: discord.TextChannel):
        """
        Unlock a channel.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Unlock {channel}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        try:
            module_enabled = settings["moderation_module"]["enabled"]
        except KeyError:
            module_enabled = False
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        
        for overwrite in channel.overwrites:
            if isinstance(overwrite, discord.Role) and not channel.permissions_for(overwrite).send_messages:
                await channel.set_permissions(overwrite, send_messages=True)
        await ctx.send(
            embed = discord.Embed(
                description = f"{channel.mention} has been unlocked.",
                color = discord.Color.green()
            )
        )
        try:
            mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        except KeyError:
            mod_log_channel = None
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "Channel Unlocked",
                    description = f"**Channel:** {channel.mention}\n**Moderator:** {ctx.author.mention}",
                    color = discord.Color.green()
                )
            )
        else:
            await ctx.channel.send(
                "Moderation log channel not found. Please set up the bot using the `config` command."
            )

    @commands.hybrid_command(
        name="purge",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        amount="Number of messages to purge (max 100)"
    )
    @premium_check()
    async def purge(self, ctx, amount: int):
        """
        Purge messages in a channel.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Purge {amount} messages")
        await ctx.typing()
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        try:
            module_enabled = settings["moderation_module"]["enabled"]
        except KeyError:
            module_enabled = False
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        
        if amount > 25:
            for i in range(0, amount, 25):
                await ctx.channel.purge(limit=25)
        else:
            await ctx.channel.purge(limit=amount)

        await ctx.send(
            embed = discord.Embed(
                description = f"{amount} messages have been purged.",
                color = discord.Color.green()
            )
        )
        try:
            mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        except KeyError:
            mod_log_channel = None
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "Messages Purged",
                    description = f"**Channel:** {ctx.channel.mention}\n**Moderator:** {ctx.author.mention}\n**Amount:** {amount}",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                "Moderation log channel not found. Please set up the bot using the `config` command."
            )


    @commands.hybrid_command(
        name="slowmode",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        seconds="Duration of the slowmode in seconds"
    )
    @premium_check()
    async def slowmode(self, ctx, seconds: int):
        """
        Set the slowmode for a channel.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Slowmode {seconds} seconds")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        try:
            module_enabled = settings["moderation_module"]["enabled"]
        except KeyError:
            module_enabled = False
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send(
                f"Slowmode has been disabled in {ctx.channel.mention}."
            )
        else:
            await ctx.send(
                f"Slowmode has been set to {seconds} seconds in {ctx.channel.mention}."
            )
        try:
            mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        except KeyError:
            mod_log_channel = None
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "Slowmode Set",
                    description = f"**Channel:** {ctx.channel.mention}\n**Moderator:** {ctx.author.mention}\n**Seconds:** {seconds}",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                "Moderation log channel not found. Please set up the bot using the `config` command."
            )


    @commands.hybrid_command(
        name="nick",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        member="Member to change nickname",
        nickname="New nickname"
    )
    @premium_check()
    async def nick(self, ctx, member: discord.Member, *, nickname: str):
        """
        Change a user's nickname.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Nick {member} {nickname}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        try:
            module_enabled = settings["moderation_module"]["enabled"]
        except KeyError:
            module_enabled = False
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        if ctx.author.top_role.position <= member.top_role.position:
            return await ctx.send(
                embed = discord.Embed(
                    title="Looks like you can't do that",
                    description="You can't change this user's nickname because they have a higher role than you.",
                    color=RED_COLOR
                )
            )

        await member.edit(nick=nickname)
        await ctx.send(
            f"{member.mention}'s nickname has been changed to `{nickname}`."
        )
        try:
            mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        except KeyError:
            mod_log_channel = None
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "Nickname Changed",
                    description = f"**User ID:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Nickname:** {nickname}",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                "Moderation log channel not found. Please set up the bot using the `config` command."
            )


    @commands.hybrid_group(
        name="role",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    async def role(self, ctx):
        """
        Manage roles.
        """
        pass

    @role.command(
        name="add",
        extras={"category": "Moderation"}
    )
    @premium_check()
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        member="Member to add role to",
        role="Role to add"
    )
    async def role_add(self, ctx, member: discord.Member, role: discord.Role):
        """
        Add a role to a user.
        """
        try:
            if ctx.author.top_role.position <= role.position:
                return await ctx.send(
                    embed = discord.Embed(
                        title="Looks like you can't do that",
                        description="You can't add this role because it is higher than your top role.",
                        color=RED_COLOR
                    )
                )
            settings = await self.bot.settings.find_by_id(ctx.guild.id)
            if not settings:
                return await ctx.send(
                    embed = discord.Embed(
                        description = "No settings found.\nPlease set up the bot using the `config` command.",
                        color = discord.Color.red()
                    )
                )
            try:
                module_enabled = settings["moderation_module"]["enabled"]
            except KeyError:
                module_enabled = False
            if not module_enabled:
                return await ctx.send(
                    embed = discord.Embed(
                        description = "Moderation module is not enabled.",
                        color = discord.Color.red()
                    )
                )
            try:
                await member.add_roles(role)
            except discord.Forbidden:
                return await ctx.send(
                    embed = discord.Embed(
                        description = "I do not have the required permissions to add this role.",
                        color = discord.Color.red()
                    )
                )
            await ctx.send(
                embed = discord.Embed(
                    description = f"{role.mention} has been added to {member.mention}.",
                    color = discord.Color.green()
                )
            )
            try:
                mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
            except KeyError:
                mod_log_channel = None
            if mod_log_channel:
                await mod_log_channel.send(
                    embed = discord.Embed(
                        title = f"{self.bot.emoji.get('moderation')} | Role Added",
                        description = f"**User ID:** {member.mention}\n**Role:** {role.mention}\n**Moderator:** {ctx.author.mention}",
                        color = discord.Color.red()
                    ).set_footer(text=f"CYNI Moderation Log | Guild: {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
                )
            else:
                await ctx.channel.send(
                    "Moderation log channel not found. Please set up the bot using the `config` command."
                )
        except Exception as e:
            await ctx.send(
                embed = discord.Embed(
                    description = f"An error occurred: {e}",
                    color = discord.Color.red()
                )
            )

    @role.command(
        name="remove",
        extras={"category": "Moderation"}
    )
    @premium_check()
    @commands.guild_only()
    @is_staff_or_management()
    @app_commands.describe(
        member="Member to remove role from",
        role="Role to remove"
    )
    async def role_remove(self, ctx, member: discord.Member, role: discord.Role):
        """
        Remove a role from a user.
        """
        try:
            if ctx.author.top_role.position <= role.position:
                return await ctx.send(
                    embed = discord.Embed(
                        title="Looks like you can't do that",
                        description="You can't remove this role because it is higher than your top role.",
                        color=RED_COLOR
                    )
                )
            if ctx.author.top_role.position <= member.top_role.position:
                return await ctx.send(
                    embed = discord.Embed(
                        title="Looks like you can't do that",
                        description="You can't remove this role because it is higher than your top role.",
                        color=RED_COLOR
                    )
                )
            settings = await self.bot.settings.find_by_id(ctx.guild.id)
            if not settings:
                return await ctx.send(
                    embed = discord.Embed(
                        description = "No settings found.\nPlease set up the bot using the `config` command.",
                        color = discord.Color.red()
                    )
                )
            try:
                module_enabled = settings["moderation_module"]["enabled"]
            except KeyError:
                module_enabled = False
            if not module_enabled:
                return await ctx.send(
                    embed = discord.Embed(
                        description = "Moderation module is not enabled.",
                        color = discord.Color.red()
                    )
                )
            try:
                await member.remove_roles(role)
            except discord.Forbidden:
                return await ctx.send(
                    embed = discord.Embed(
                        description = "I do not have the required permissions to remove this role.",
                        color = discord.Color.red()
                    )
                )
            
            await ctx.send(
                embed = discord.Embed(
                    description = f"{role.mention} has been removed from {member.mention}.",
                    color = discord.Color.green()
                )
            )
            try:
                mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
            except KeyError:
                mod_log_channel = None
            if mod_log_channel:
                await mod_log_channel.send(
                    embed = discord.Embed(
                        title = "Role Removed",
                        description = f"**User ID:** {member.mention}\n**Role:** {role.mention}\n**Moderator:** {ctx.author.mention}",
                        color = discord.Color.green()
                    )
                )
            else:
                await ctx.channel.send(
                    "Moderation log channel not found. Please set up the bot using the `config` command."
                )
        except Exception as e:
            await ctx.send(
                embed = discord.Embed(
                    description = f"An error occurred: {e}",
                    color = discord.Color.red()
                )
            )
            
    @role.command(
        name="all",
        extras={"category": "Moderation"},
    )
    @commands.guild_only()
    @is_management()
    @app_commands.describe(
        role="Role to add"
    )
    @premium_check()
    async def role_all(self, ctx, role: discord.Role):
        '''
        Add a role to all members in the server.
        '''
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Add role {role.mention} to all members")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = RED_COLOR
                )
            )
        try:
            module_enabled = settings["moderation_module"]["enabled"]
        except KeyError:
            module_enabled = False
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = RED_COLOR
                )
            )
        
        msg = await ctx.send(
            embed = discord.Embed(
                description = f"Added {role.mention} to all members.\nEstimated time: {len(ctx.guild.members) * 0.5} seconds",
                color = YELLOW_COLOR
            )
        )
        if ctx.author.top_role.position <= role.position:
            return await ctx.send(
                embed = discord.Embed(
                    title="Looks like you can't do that",
                    description="You can't add this role because it is higher than your top role.",
                    color=RED_COLOR
                )
            )

        for member in ctx.guild.members:
            if role in member.roles:
                continue
            try:
                await member.add_roles(role)
                await asyncio.sleep(0.5)
            except discord.Forbidden:
                return await ctx.send(
                    embed = discord.Embed(
                        description = "I do not have the required permissions to add this role.",
                        color = RED_COLOR
                    )
                )

        await asyncio.sleep(len(ctx.guild.members) * 0.5)

        await msg.edit(
            embed = discord.Embed(
                description = f"Added {role.mention} to all members.",
                color = YELLOW_COLOR
            )
        
        )
        try:
            mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        except KeyError:
            mod_log_channel = None
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "Role Added to All Members",
                    description = f"**Role:** {role.mention}\n**Moderator:** {ctx.author.mention}",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                "Moderation log channel not found. Please set up the bot using the `config` command."
            )

    @commands.hybrid_command(
        name="softban",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_management()
    @app_commands.describe(
        member="Member to softban",
        reason="Reason for softban"
    )
    @premium_check()
    async def softban(self, ctx, member: discord.Member, *, reason: str):
        """
        Softban a user.
        """
        if ctx.author.top_role.position <= member.top_role.position:
            return await ctx.send(
                embed = discord.Embed(
                    title="Looks like you can't do that",
                    description="You can't softban this user because they have a higher role than you.",
                    color=RED_COLOR
                )
            )
        if ctx.author.top_role.position <= ctx.guild.me.top_role.position:
            return await ctx.send(
                embed = discord.Embed(
                    title="Looks like you can't do that",
                    description="I can't softban this user because they have a higher role than me.",
                    color=RED_COLOR
                )
            )
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Softban {member}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        module_enabled = settings.get("moderation_module",{}).get("enabled",False)
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        try:
            await member.ban(reason=reason)
            await member.unban(reason=reason)
        except discord.Forbidden:
            return await ctx.send(
                embed = discord.Embed(
                    description = "I do not have the required permissions to softban this user.",
                    color = discord.Color.red()
                )
            )
        total_warnings = await self.bot.warnings.find(
            {
                'guild_id': ctx.guild.id,
            }
        )
        total_warnings = len(total_warnings)
        doc = {
            'guild_id': ctx.guild.id,
            'user_id': member.id,
            'reason': reason,
            'moderator_id': ctx.author.id,
            'timestamp': datetime.now().timestamp(),
            'case_id': total_warnings + 1,
            'active': True,
            'void': False,
            'type': 'softban',
        }
        await self.bot.warnings.insert_one(doc)
        await ctx.send(
            embed = discord.Embed(
                title=f"Case ID: {total_warnings + 1}",
                description = f"{member.mention} has been softbanned for `{reason}`.",
                color = GREEN_COLOR
            )
        )
        mod_log_channel = ctx.guild.get_channel(settings.get("moderation_module",{}).get("mod_log_channel",0))
        if mod_log_channel != 0:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = f"Case ID: {total_warnings + 1} | User Softbanned",
                    description = f"**User ID:** {member.mention}\n> **Moderator:** {ctx.author.mention}\n> **Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                embed=discord.Embed(
                    description = "Moderation log channel not found. Please set up the bot using the `config` command.",
                    color = RED_COLOR
                )
            )

        await member.send(
            embed = discord.Embed(
                title = f"You have been softbanned in {ctx.guild.name}",
                description = f"**Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                color = RED_COLOR
            )
        )

    #These commands are depricated and removed from the moderation module
    #Use CYNI Ban Appeal instead
    # @commands.hybrid_group(
    #     name="appeal",
    #     extras={"category": "Moderation"}
    # )
    # async def appeal(self, ctx):
    #     """
    #     Appeal a moderation action.
    #     """
    #     pass

    # @appeal.command(
    #     name="approve",
    #     extras={"category": "Moderation"}
    # )
    # @commands.has_permissions(manage_guild=True)
    # async def appeal_approve(self, ctx, user_id: str):
    #     """
    #     Approve a ban appeal.
    #     """
    #     user_id = int(user_id)
    #     uid_guild_id = f"{user_id}-{ctx.guild.id}"
        
    #     try:
    #         ban_appeal = await self.bot.ban_appeals.find_by_id(uid_guild_id)

    #         if not ban_appeal:
    #             return await ctx.send(
    #                 embed=discord.Embed(
    #                     description="No appeals found.",
    #                     color=discord.Color.red()
    #                 )
    #             )
            
    #         await ctx.guild.unban(discord.Object(id=user_id))
    #         await self.bot.ban_appeals.delete_by_id(uid_guild_id)
    #         await ctx.send(
    #             embed=discord.Embed(
    #                 description="Appeal approved.\nUser has been unbanned.",
    #                 color=discord.Color.green()
    #             ).add_field(
    #                 name="User Mention",
    #                 value=f"<@{user_id}>"
    #             )
    #         )
    #         #Get user by user_id and send them a message
    #         user = self.bot.get_user(user_id)
    #         guild_invite_link = await ctx.guild.text_channels[0].create_invite()
    #         if user:
    #             try:
    #                 await user.send(
    #                     embed=discord.Embed(
    #                         description=f"Your appeal has been approved.\nYou have been unbanned in the {ctx.guild.name} ",
    #                         color=discord.Color.green()
    #                     ).add_field(
    #                         name="Invite Link",
    #                         value=guild_invite_link
    #                     )
    #                 )
    #             except discord.Forbidden:
    #                 pass
    #         else:
    #             pass

    #     except Exception as e:
    #         await ctx.send(
    #             embed=discord.Embed(
    #                 description=f"An error occurred: {e}",
    #                 color=discord.Color.red()
    #             )
    #         )

    # @appeal.command(
    #     name="deny",
    #     extras={"category": "Moderation"}
    # )
    # @commands.has_permissions(manage_guild=True)
    # async def appeal_deny(self, ctx, user_id: str):
    #     """
    #     Deny a ban appeal.
    #     """
    #     user_id = int(user_id)
    #     uid_guild_id = f"{user_id}-{ctx.guild.id}"

    #     try:
    #         ban_appeal = await self.bot.ban_appeals.find_by_id(uid_guild_id)
            
    #         if not ban_appeal:
    #             return await ctx.send(
    #                 embed=discord.Embed(
    #                     description="No appeals found.",
    #                     color=discord.Color.red()
    #                 )
    #             )
            
    #         await self.bot.ban_appeals.delete_by_id(uid_guild_id)
    #         await ctx.send(
    #             embed=discord.Embed(
    #                 description="Appeal denied.",
    #                 color=discord.Color.green()
    #             ).add_field(
    #                 name="User Mention",
    #                 value=f"<@{user_id}>"
    #             )
    #         )
    #         #Get user by user_id and send them a message
    #         user = self.bot.get_user(user_id)
    #         if user:
    #             try:
    #                 await user.send(
    #                     embed=discord.Embed(
    #                         description=f"Your appeal has been denied in the {ctx.guild.name}.",
    #                         color=discord.Color.red()
    #                     )
    #                 )
    #             except discord.Forbidden:
    #                 pass
    #         else:
    #             pass

    #     except Exception as e:
    #         await ctx.send(
    #             embed=discord.Embed(
    #                 description=f"An error occurred: {e}",
    #                 color=discord.Color.red()
    #             )
    #         )

    @commands.hybrid_command(
        name="temprole",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_management()
    @app_commands.describe(
        member="Member to assign role to",
        role="Role to assign",
        duration="Duration to assign role for"
    )
    @premium_check()
    async def temprole(self, ctx, member: discord.Member, role: discord.Role, duration: str):
        """
        Temporarily assign a role to a user.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Temprole {member} {role} {duration}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        try:
            module_enabled = settings["moderation_module"]["enabled"]
        except KeyError:
            module_enabled = False
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        
        if ctx.author.top_role.position <= role.position:
            return await ctx.send(
                embed = discord.Embed(
                    title="Looks like you can't do that",
                    description="You can't add this role because it is higher than your top role.",
                    color=RED_COLOR
                )
            )
                
        duration = parse_duration(duration)
        if duration is None:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Invalid duration format. Please use a valid format.",
                    color = discord.Color.red()
                )
            )
        
        doc = {
            'guild_id': ctx.guild.id,
            'user_id': member.id,
            'role_id': role.id,
            'expire_at': datetime.now().timestamp() + duration,
            'reason': f"Temprole {role.name} for {duration} seconds",
            'timestamp': datetime.now().timestamp(),
            'active': True,
            'completed': False,
            'void': False
        }
        await self.bot.temp_roles.insert_one(doc)

        try:
            await member.add_roles(role)
        except discord.Forbidden:
            return await ctx.send(
                embed = discord.Embed(
                    description = "I do not have the required permissions to add this role.",
                    color = discord.Color.red()
                )
            )

        await ctx.send(
            embed = discord.Embed(
                description = f"{role.mention} has been added to {member.mention} for {duration} seconds.",
                color = GREEN_COLOR
            )
        )

        try:
            mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        except KeyError:
            mod_log_channel = None
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "Role Added Temporarily",
                    description = f"**User ID:** {member.mention}\n**Role:** {role.mention}\n**Moderator:** {ctx.author.mention}\n**Duration:** {duration} seconds",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                embed=discord.Embed(
                    description = "Moderation log channel not found. Please set up the bot using the `config` command.",
                    color = RED_COLOR
                )
            )
        #role will be removed using discord.py's built in task loop

async def setup(bot):
    await bot.add_cog(Moderation(bot))
