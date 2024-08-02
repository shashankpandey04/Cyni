import discord
from discord.ext import commands

from Datamodels.Warning import Warnings
from cyni import is_staff_or_management,is_management
from utils.Schema import warning
from utils.utils import log_command_usage
from datetime import timedelta, datetime
import re

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
                    color = discord.Color.red()
                )
            )
        module_enabled = settings["moderation_module"]["enabled"]
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "<:moderation:1268850116798844969> Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        if member == ctx.author:
            return await ctx.send(
                embed = discord.Embed(
                    description = "<:moderation:1268850116798844969> You cannot warn yourself.",
                    color = discord.Color.red()
                )
            )
        user_warnings = await self.warnings.find_by_id(f"{ctx.guild.id}-{member.id}")
        if not user_warnings:
            user_warnings = warning.copy()
            user_warnings["_id"] = f"{ctx.guild.id}-{member.id}"

        user_warnings["warnings"].append({
            "reason": reason,
            "moderator": ctx.author.id,
            "timestamp": f"{ctx.message.created_at}"
        })
        user_warnings["_id"] = f"{ctx.guild.id}-{member.id}"
        await self.warnings.update_by_id(user_warnings)
        await ctx.send(
            embed = discord.Embed(
                description = f"<:moderation:1268850116798844969> {member.mention} has been warned for `{reason}`.\nCase ID: {len(user_warnings['warnings'])}",
                color = discord.Color.green()
            )
        )
        await member.send(
            embed = discord.Embed(
                title = f"You have been warned in {ctx.guild.name}",
                description = f"Reason: {reason}\n",
                color = discord.Color.red()
            )
        )
        log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        if log_channel:
            await log_channel.send(
                embed = discord.Embed(
                    title = "Warning",
                    description = f"**User:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                "<:moderation:1268850116798844969> Moderation log channel not found. Please set up the bot using the `config` command."
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
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Get warnings for {member}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        module_enabled = settings["moderation_module"]["enabled"]
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "<:moderation:1268850116798844969> Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        user_warnings = await self.warnings.find_by_id(f"{ctx.guild.id}-{member.id}")
        if not user_warnings:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"<:moderation:1268850116798844969> {member.mention} has no warnings.",
                    color = discord.Color.green()
                )
            )
        embed = discord.Embed(
            title = f"Warnings for {member}",
            color = discord.Color.blurple()
        )
        for index, warning in enumerate(user_warnings["warnings"]):
            embed.add_field(
                name = f"Case {index + 1}",
                value = f"Reason: {warning['reason']}\nModerator: <@{warning['moderator']}>\nTimestamp: {warning['timestamp']}",
                inline = False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="clearwarns",
        aliases=["cw"],
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    async def clearwarns(self, ctx, member: discord.Member):
        """
        Clear the warnings for a user.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Clear warnings for {member}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        module_enabled = settings["moderation_module"]["enabled"]
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "<:moderation:1268850116798844969> Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        user_warnings = await self.warnings.find_by_id(f"{ctx.guild.id}-{member.id}")
        if not user_warnings:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"<:moderation:1268850116798844969> {member.mention} has no warnings.",
                    color = discord.Color.green()
                )
            )
        await self.warnings.delete_by_id(f"{ctx.guild.id}-{member.id}")
        await ctx.send(
            embed = discord.Embed(
                description = f"<:moderation:1268850116798844969> {member.mention}'s warnings have been cleared.",
                color = discord.Color.green()
            )
        )

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "Warnings Cleared",
                    description = f"**User ID:** {member.mention}\n**Moderator:** {ctx.author.mention}",
                    color = discord.Color.green()
                )
            )
        else:
            await ctx.channel.send(
                "<:moderation:1268850116798844969> Moderation log channel not found. Please set up the bot using the `config` command."
            )

    @commands.hybrid_command(
        name="delwarn",
        aliases=["dw"],
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    async def delwarn(self, ctx, member: discord.Member, case: int):
        """
        Delete a warning for a user.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Delete warning {case} for {member}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        module_enabled = settings["moderation_module"]["enabled"]
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "<:moderation:1268850116798844969> Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        user_warnings = await self.warnings.find_by_id(f"{ctx.guild.id}-{member.id}")
        if not user_warnings:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{member.mention} has no warnings.",
                    color = discord.Color.green()
                )
            )
        if case > len(user_warnings["warnings"]):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"<:moderation:1268850116798844969> {member.mention} has no warning with case ID {case}.",
                    color = discord.Color.red()
                )
            )
        user_warnings["warnings"].pop(case - 1)
        await self.warnings.update_by_id(user_warnings)
        await ctx.send(
            embed = discord.Embed(
                description = f"Warning {case} for {member.mention} has been deleted.",
                color = discord.Color.green()
            )
        )

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "Warning Deleted",
                    description = f"**User ID:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Case ID:** {case}",
                    color = discord.Color.green()
                )
            )
        else:
            await ctx.channel.send(
                "<:moderation:1268850116798844969> Moderation log channel not found. Please set up the bot using the `config` command."
            )

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
        module_enabled = settings["moderation_module"]["enabled"]
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        await member.kick(reason=reason)
        await ctx.send(
            f"{member.mention} has been kicked ✅."
        )

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "User Kicked",
                    description = f"**User ID:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
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
        module_enabled = settings["moderation_module"]["enabled"]
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        
        await member.ban(reason=reason)
        await ctx.send(
            embed = discord.Embed(
                description = f"{member.mention} has been banned for `{reason}`.",
                color = discord.Color.green()
            )
        )

        try:
            await member.send(
                embed = discord.Embed(
                    title = f"You have been banned in {ctx.guild.name}",
                    description = f"**Moderator:** {ctx.author.mention}\n**Reason:** {reason}\n**Guild ID:** {ctx.guild.id}",
                    color = discord.Color.red()
                )
            )
        except discord.Forbidden:
            pass

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "User Banned",
                    description = f"**User ID:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                "Moderation log channel not found. Please set up the bot using the `config` command."
            )

    @commands.hybrid_command(
        name="unban",
        extras={"category": "Moderation"}
    )
    @commands.guild_only()
    @is_staff_or_management()
    async def unban(self, ctx, userid:str, *, reason: str):
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
        module_enabled = settings["moderation_module"]["enabled"]
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
        await ctx.send(
            embed = discord.Embed(
                description = f"{member.mention} has been unbanned for `{reason}`.",
                color = discord.Color.green()
            )
        )

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "User Unbanned",
                    description = f"**User ID:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                    color = discord.Color.green()
                )
            )
        else:
            await ctx.channel.send(
                "Moderation log channel not found. Please set up the bot using the `config` command."
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
        def parse_duration(self, duration):
            """
            Parse a duration string and return the total duration in seconds.
            Supports days (d), weeks (w), hours (h), minutes (m), and seconds (s).
            """
            regex = r"(?:(\d+)\s*d(?:ays?)?)?\s*(?:(\d+)\s*w(?:eeks?)?)?\s*(?:(\d+)\s*h(?:ours?)?)?\s*(?:(\d+)\s*m(?:inutes?)?)?\s*(?:(\d+)\s*s(?:econds?)?)?"
            matches = re.match(regex, duration)
            if not matches:
                return None

            days = int(matches.group(1)) if matches.group(1) else 0
            weeks = int(matches.group(2)) if matches.group(2) else 0
            hours = int(matches.group(3)) if matches.group(3) else 0
            minutes = int(matches.group(4)) if matches.group(4) else 0
            seconds = int(matches.group(5)) if matches.group(5) else 0

            total_seconds = timedelta(days=days, weeks=weeks, hours=hours, minutes=minutes, seconds=seconds).total_seconds()
            return int(total_seconds)
        
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Mute {member}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        module_enabled = settings["moderation_module"]["enabled"]
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        time = parse_duration(self,time)
        member.timed_out_until = datetime.datetime.now() + datetime.timedelta(seconds=time)

        await ctx.send(
            embed = discord.Embed(
                description = f"{member.mention} has been muted for `{reason}`.",
                color = discord.Color.green()
            )
        )

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "User Muted",
                    description = f"**User ID:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                "Moderation log channel not found. Please set up the bot using the `config` command."
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
        module_enabled = settings["moderation_module"]["enabled"]
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        member.timed_out_until = None
        await ctx.send(
            embed = discord.Embed(
                description = f"{member.mention} has been unmuted for `{reason}`.",
                color = discord.Color.green()
            )
        )

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "User Unmuted",
                    description = f"**User ID:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                    color = discord.Color.green()
                )
            )
        else:
            await ctx.channel.send(
                "Moderation log channel not found. Please set up the bot using the `config` command."
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
        module_enabled = settings["moderation_module"]["enabled"]
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

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
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
        module_enabled = settings["moderation_module"]["enabled"]
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )
        
        for role in ctx.guild.roles:
            if not channel.permissions_for(role).send_messages:
                await channel.set_permissions(role, send_messages=True)
        await ctx.send(
            embed = discord.Embed(
                description = f"{channel.mention} has been unlocked.",
                color = discord.Color.green()
            )
        )

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
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
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Purge {amount} messages")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        module_enabled = settings["moderation_module"]["enabled"]
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

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
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
        module_enabled = settings["moderation_module"]["enabled"]
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

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
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
        module_enabled = settings["moderation_module"]["enabled"]
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    description = "Moderation module is not enabled.",
                    color = discord.Color.red()
                )
            )

        await member.edit(nick=nickname)
        await ctx.send(
            f"{member.mention}'s nickname has been changed to `{nickname}`."
        )

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
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
            settings = await self.bot.settings.find_by_id(ctx.guild.id)
            if not settings:
                return await ctx.send(
                    embed = discord.Embed(
                        description = "No settings found.\nPlease set up the bot using the `config` command.",
                        color = discord.Color.red()
                    )
                )
            module_enabled = settings["moderation_module"]["enabled"]
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

            mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
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
            settings = await self.bot.settings.find_by_id(ctx.guild.id)
            if not settings:
                return await ctx.send(
                    embed = discord.Embed(
                        description = "No settings found.\nPlease set up the bot using the `config` command.",
                        color = discord.Color.red()
                    )
                )
            
            module_enabled = settings["moderation_module"]["enabled"]
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

            mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
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
        
        module_enabled = settings["moderation_module"]["enabled"]
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
        await ctx.send(
            embed = discord.Embed(
                description = f"{member.mention} has been softbanned for `{reason}`.",
                color = discord.Color.green()
            )
        )

        mod_log_channel = ctx.guild.get_channel(settings["moderation_module"]["mod_log_channel"])
        if mod_log_channel:
            await mod_log_channel.send(
                embed = discord.Embed(
                    title = "User Softbanned",
                    description = f"**User ID:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                    color = discord.Color.red()
                )
            )
        else:
            await ctx.channel.send(
                "Moderation log channel not found. Please set up the bot using the `config` command."
            )

    @commands.hybrid_group(
        name="appeal",
        extras={"category": "Moderation"}
    )
    async def appeal(self, ctx):
        """
        Appeal a moderation action.
        """
        pass

    @appeal.command(
        name="approve",
        extras={"category": "Moderation"}
    )
    @commands.has_permissions(manage_guild=True)
    async def appeal_approve(self, ctx, user_id: str):
        """
        Approve a ban appeal.
        """
        user_id = int(user_id)
        uid_guild_id = f"{user_id}-{ctx.guild.id}"
        
        try:
            ban_appeal = await self.bot.ban_appeals.find_by_id(uid_guild_id)

            if not ban_appeal:
                return await ctx.send(
                    embed=discord.Embed(
                        description="No appeals found.",
                        color=discord.Color.red()
                    )
                )
            
            await ctx.guild.unban(discord.Object(id=user_id))
            await self.bot.ban_appeals.delete_by_id(uid_guild_id)
            await ctx.send(
                embed=discord.Embed(
                    description="Appeal approved.\nUser has been unbanned.",
                    color=discord.Color.green()
                ).add_field(
                    name="User Mention",
                    value=f"<@{user_id}>"
                )
            )
            #Get user by user_id and send them a message
            user = self.bot.get_user(user_id)
            guild_invite_link = await ctx.guild.text_channels[0].create_invite()
            if user:
                try:
                    await user.send(
                        embed=discord.Embed(
                            description=f"Your appeal has been approved.\nYou have been unbanned in the {ctx.guild.name} ",
                            color=discord.Color.green()
                        ).add_field(
                            name="Invite Link",
                            value=guild_invite_link
                        )
                    )
                except discord.Forbidden:
                    pass
            else:
                pass

        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    description=f"An error occurred: {e}",
                    color=discord.Color.red()
                )
            )

    @appeal.command(
        name="deny",
        extras={"category": "Moderation"}
    )
    @commands.has_permissions(manage_guild=True)
    async def appeal_deny(self, ctx, user_id: str):
        """
        Deny a ban appeal.
        """
        user_id = int(user_id)
        uid_guild_id = f"{user_id}-{ctx.guild.id}"

        try:
            ban_appeal = await self.bot.ban_appeals.find_by_id(uid_guild_id)
            
            if not ban_appeal:
                return await ctx.send(
                    embed=discord.Embed(
                        description="No appeals found.",
                        color=discord.Color.red()
                    )
                )
            
            await self.bot.ban_appeals.delete_by_id(uid_guild_id)
            await ctx.send(
                embed=discord.Embed(
                    description="Appeal denied.",
                    color=discord.Color.green()
                ).add_field(
                    name="User Mention",
                    value=f"<@{user_id}>"
                )
            )
            #Get user by user_id and send them a message
            user = self.bot.get_user(user_id)
            if user:
                try:
                    await user.send(
                        embed=discord.Embed(
                            description=f"Your appeal has been denied in the {ctx.guild.name}.",
                            color=discord.Color.red()
                        )
                    )
                except discord.Forbidden:
                    pass
            else:
                pass

        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    description=f"An error occurred: {e}",
                    color=discord.Color.red()
                )
            )

async def setup(bot):
    await bot.add_cog(Moderation(bot))
