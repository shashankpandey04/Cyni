import discord
from discord.ext import commands

from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR, YELLOW_COLOR
from Datamodels.Warning import Warnings
from cyni import is_staff_or_management,is_management
from utils.Schema import warning
from utils.utils import log_command_usage
from datetime import timedelta, datetime
from utils.utils import parse_duration
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = Warnings(bot.db,"warnings")

    @commands.hybrid_command(
        name="warn",
        aliases=["w"],
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    async def warn(self, ctx, member: discord.Member, *, reason: str):
        """
        Warn a user.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Warn {member}")
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
                    description = "<:moderation:1268850116798844969> Moderation module is not enabled.",
                    color = RED_COLOR
                )
            )
        if member == ctx.author:
            return await ctx.send(
                embed = discord.Embed(
                    description = "<:moderation:1268850116798844969> You cannot warn yourself.",
                    color = RED_COLOR
                )
            )

        total_warnings = await self.warnings.find(
            {
                'guild_id': ctx.guild.id,
            }
        )
        total_warnings = len(total_warnings)

        doc ={
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

        await self.warnings.insert_one(doc)
        await ctx.send(
            embed = discord.Embed(
                description = f"<:moderation:1268850116798844969> {member.mention} has been warned for `{reason}`.\nCase ID: {total_warnings + 1}",
                color = GREEN_COLOR
            )
        )
        await member.send(
            embed = discord.Embed(
                description = f"You have been warned in **{ctx.guild.name}**\n\n**Case ID:** {total_warnings + 1}\n> **Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                color = RED_COLOR
            )
        )
        log_channel = ctx.guild.get_channel(settings.get("moderation_module",{}).get("mod_log_channel",0))
        if log_channel != 0:
            await log_channel.send(
                embed = discord.Embed(
                    title = f"Case {total_warnings + 1} | Warn",
                    description = f"**User:** {member.mention}\n> **Moderator:** {ctx.author.mention}\n> **Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                    color = GREEN_COLOR
                )
            )
        else:
            embed = discord.Embed(
                description = "<:moderation:1268850116798844969> Moderation log channel not found. Please set up the bot using the `config` command.",
                color = RED_COLOR
            )
            await ctx.channel.send(
                embed = embed
            )

    @commands.hybrid_command(
        name="warnings",
        aliases=["warns"],
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    async def warnings(self, ctx, member: discord.Member):
        """
        Get the warnings for a user.
        """
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
                    description = "<:moderation:1268850116798844969> Moderation module is not enabled.",
                    color = RED_COLOR
                )
            )
        user_warnings = await self.warnings.find_one(
            {
                'guild_id': ctx.guild.id,
                'user_id': member.id,
            }
        )
        if not user_warnings:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"<:moderation:1268850116798844969> {member.mention} has no warnings.",
                    color = GREEN_COLOR
                )
            )
        embed = discord.Embed(
            title = f"{member.name}'s Warnings",
            description=" ",
            color = RED_COLOR
        )
        for warning in user_warnings["warnings"]:
            embed.description += f"**Case ID:** {warning['case_id']}\n> **Reason:** {warning['reason']}\n> **Moderator:** <@{warning['moderator_id']}>\n> **Type:** {warning['type']}\n> **Timestamp:** <t:{int(warning['timestamp'])}:R>\n> **Status:** {'Active' if warning['active'] else 'Void'}\n\n"

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="void",
        aliases=["v"],
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
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
                    description = "<:moderation:1268850116798844969> Moderation module is not enabled.",
                    color = RED_COLOR
                )
            )
        user_warning = await self.warnings.find_one(
            {
                'guild_id': ctx.guild.id,
                'case_id': case,
            }
        )
        if not user_warning:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"<:moderation:1268850116798844969> Warning with case ID {case} not found.",
                    color = GREEN_COLOR
                )
            )
        user_warning['active'] = False
        user_warning['void'] = True
        await self.warnings.update_by_id(user_warning)
        await ctx.send(
            embed = discord.Embed(
                description = f"<:moderation:1268850116798844969> Warning with case ID {case} has been voided.",
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
                    description = "<:moderation:1268850116798844969> Moderation log channel not found. Please set up the bot using the `config` command.",
                    color = RED_COLOR
                )
            )

    @commands.hybrid_command(
    name='case',
    extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
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
                    description="<:moderation:1268850116798844969> Moderation module is not enabled.",
                    color=RED_COLOR
                )
            )
        
        user_warning = await self.warnings.find_one(
            {
                'guild_id': ctx.guild.id,
                'case_id': case,
            }
        )
        
        if not user_warning:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"<:moderation:1268850116798844969> Warning with case ID {case} not found.",
                    color=GREEN_COLOR
                )
            )
        
        embed = discord.Embed(
            title=f"Case ID: {case}",
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

        total_warnings = await self.warnings.find(
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
        await self.warnings.insert_one(doc)

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
                    title = "Case ID: {total_warnings + 1} | User Kicked",
                    description = f"**User ID:** {member.mention}\n> **Moderator:** {ctx.author.mention}\n> **Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                "Moderation log channel not found. Please set up the bot using the `config` command."
            )

    @commands.hybrid_command(
        name="ban",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    async def ban(self, ctx, member: discord.Member, *, reason: str):
        """
        Ban a user.
        """
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
        
        total_warnings = await self.warnings.find(
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
        await self.warnings.insert_one(doc)

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
        member = discord.Object(id=userid)
        await ctx.guild.unban(member, reason=reason)

        total_warnings = await self.warnings.find(
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
        await self.warnings.insert_one(doc)

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
    async def mute(self, ctx, member: discord.Member, time:str, reason: str):
        """
        Mute a user.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Mute {member} for {time}")
        print(time)
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
        time = parse_duration(time)
        if not time:
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
        time = discord.utils.utcnow() + timedelta(seconds=time)
        try:
            await member.edit(timed_out_until=time, reason=reason)
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
        total_warnings = await self.warnings.find(
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
        }

        await self.warnings.insert_one(doc)
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
                    description = f"**User ID:** {member.mention}\n> **Moderator:** {ctx.author.mention}\n> **Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
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
                description = f"**Reason:** {reason}\n> **Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                color = RED_COLOR
            )
        )

    @commands.hybrid_command(
        name="unmute",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
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
        total_warnings = await self.warnings.find(
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
        await self.warnings.insert_one(doc)
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
    async def purge(self, ctx, amount: int):
        """
        Purge messages in a channel.
        
        Discord only allows bulk deletion of messages that are less than 14 days old.
        Older messages will be deleted individually at a slower rate.
        
        Parameters:
        -----------
        amount: int
            The number of messages to delete (max 500)
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Purge {amount} messages")
            
        # Check for valid amount
        if amount <= 0:
            return await ctx.send(
                embed=discord.Embed(
                    description="Please provide a positive number of messages to delete.",
                    color=discord.Color.red()
                )
            )
            
        if amount > 500:
            return await ctx.send(
                embed=discord.Embed(
                    description="For safety reasons, you cannot purge more than 500 messages at once.",
                    color=discord.Color.red()
                )
            )
        
        # Defer response for longer operations
        if hasattr(ctx, 'defer'):
            await ctx.defer(ephemeral=True)
        else:
            await ctx.typing()
        
        # Check settings
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
        
        # Get current time for age check
        two_weeks_ago = datetime.now() - timedelta(days=14)
        
        # Collection to track deleted messages counts
        deleted_count = 0
        recent_count = 0
        old_count = 0
        
        status_message = await ctx.send(
            embed=discord.Embed(
                description=f"Purging {amount} messages...",
                color=discord.Color.orange()
            )
        )
        
        try:
            # First, fetch messages to analyze them
            messages = []
            async for message in ctx.channel.history(limit=amount + 1):  # +1 to account for the command message
                if message.id != ctx.message.id:  # Skip the command message
                    messages.append(message)
                if len(messages) >= amount:
                    break
                    
            if not messages:
                return await status_message.edit(
                    embed=discord.Embed(
                        description="No messages found to delete.",
                        color=discord.Color.orange()
                    )
                )
                
            # Separate messages by age
            recent_messages = []
            old_messages = []
            
            for message in messages:
                if message.created_at > two_weeks_ago:
                    recent_messages.append(message)
                else:
                    old_messages.append(message)
            
            # Process recent messages in bulk (100 at a time to avoid rate limits)
            if recent_messages:
                for i in range(0, len(recent_messages), 100):
                    chunk = recent_messages[i:i+100]
                    await ctx.channel.delete_messages(chunk)
                    recent_count += len(chunk)
                    # Update status every 100 messages
                    if i % 100 == 0 and i > 0:
                        await status_message.edit(
                            embed=discord.Embed(
                                description=f"Processed {recent_count + old_count}/{amount} messages...",
                                color=discord.Color.orange()
                            )
                        )
                        await asyncio.sleep(1)  # Brief pause to avoid rate limiting
                
            # Process old messages individually with rate limiting
            if old_messages:
                await status_message.edit(
                    embed=discord.Embed(
                        description=f"Deleted {recent_count} recent messages. Now processing {len(old_messages)} older messages (this will be slower)...",
                        color=discord.Color.orange()
                    )
                )
                
                for i, message in enumerate(old_messages):
                    try:
                        await message.delete()
                        old_count += 1
                        
                        # Update status every 10 messages
                        if (i + 1) % 10 == 0:
                            await status_message.edit(
                                embed=discord.Embed(
                                    description=f"Processed {recent_count + old_count}/{amount} messages... ({old_count} older messages)",
                                    color=discord.Color.orange()
                                )
                            )
                            
                        # Wait to avoid rate limits (5 deletes per 5 seconds is safe)
                        if (i + 1) % 5 == 0:
                            await asyncio.sleep(1)
                            
                    except discord.NotFound:
                        # Message already deleted
                        pass
                    except discord.Forbidden:
                        await status_message.edit(
                            embed=discord.Embed(
                                description=f"⚠️ Missing permissions to delete some messages. Deleted {recent_count + old_count} messages total.",
                                color=discord.Color.red()
                            )
                        )
                        break
                    except discord.HTTPException as e:
                        if e.code == 429:  # Rate limited
                            retry_after = e.retry_after if hasattr(e, 'retry_after') else 5
                            await status_message.edit(
                                embed=discord.Embed(
                                    description=f"Rate limited. Waiting {retry_after:.1f}s...",
                                    color=discord.Color.orange()
                                )
                            )
                            await asyncio.sleep(retry_after)
                            # Try again
                            try:
                                await message.delete()
                                old_count += 1
                            except:
                                pass
                        else:
                            # Other HTTP error, continue with next message
                            continue
            
            deleted_count = recent_count + old_count
            
            # Final status
            await status_message.edit(
                embed=discord.Embed(
                    description=f"✅ Successfully deleted {deleted_count} messages.\n• {recent_count} recent messages\n• {old_count} older messages (>14 days)",
                    color=discord.Color.green()
                )
            )
            
        except Exception as e:
            await status_message.edit(
                embed=discord.Embed(
                    description=f"An error occurred: {str(e)}\nDeleted {deleted_count} messages before the error.",
                    color=discord.Color.red()
                )
            )
        
        # Log the action
        try:
            mod_log_channel = ctx.guild.get_channel(settings["moderation_module"].get("mod_log_channel"))
            if mod_log_channel:
                await mod_log_channel.send(
                    embed=discord.Embed(
                        title="Messages Purged",
                        description=f"**Channel:** {ctx.channel.mention}\n**Moderator:** {ctx.author.mention}\n**Amount:** {deleted_count}/{amount} messages\n**Recent:** {recent_count}\n**Older:** {old_count}",
                        color=discord.Color.red()
                    ).set_footer(text=f"Moderator ID: {ctx.author.id}")
                )
        except Exception:
            pass

    @commands.hybrid_command(
        name="slowmode",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
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
    @is_staff_or_management()
    async def role(self, ctx):
        """
        Manage roles.
        """
        pass

    @role.command(
        name="add",
        extras={"category": "Moderation"}
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
                        title = "Role Added",
                        description = f"**User ID:** {member.mention}\n**Role:** {role.mention}\n**Moderator:** {ctx.author.mention}",
                        color = discord.Color.red()
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
        name="remove",
        extras={"category": "Moderation"}
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
        total_warnings = await self.warnings.find(
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
        await self.warnings.insert_one(doc)
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
