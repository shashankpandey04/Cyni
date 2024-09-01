import discord
import time
from discord.ext import commands

from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
import datetime

class OnGuildRoleUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """
        This event is triggered when a role is updated in a guild.
        :param before (discord.Role): The role before the update.
        :param after (discord.Role): The role after the update.
        """
            
        sett = await self.bot.settings.find_by_id(after.guild.id)
        guild = after.guild
        if not sett:
            return
        try:
            if not sett["moderation_module"]["enabled"]:
                return
        except KeyError:
            return
        try:
            if not sett["moderation_module"]["enabled"]:
                return
        except KeyError:
            return
        try:
            if not sett["moderation_module"]["audit_log"]:
                return
        except KeyError:
            return
        guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])
        created_at = discord_time(datetime.datetime.now())

        if before.name != after.name:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                return await guild_log_channel.send(
                    embed = discord.Embed(
                        title= " ",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Before",
                        value=f"{before.name}",
                    ).add_field(
                        name="After",
                        value=f"{after.name}",
                    ).set_footer(
                        text=f"Role ID: {after.id}"
                    )
                )

        if before.color != after.color:
            for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                return await guild_log_channel.send(
                    embed = discord.Embed(
                        title= "Role Color Update",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Before",
                        value=f"{before.color}",
                    ).add_field(
                        name="After",
                        value=f"{after.color}",
                    ).set_footer(
                        text=f"Role ID: {after.id}"
                    )
                )

        if before.permissions != after.permissions:
            for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                return await guild_log_channel.send(
                    embed = discord.Embed(
                        title= " ",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Role Permissions",
                        value=f"{before.permissions} -> {after.permissions}",
                    ).set_footer(
                        text=f"Role ID: {after.id}"
                    )
                )

        if before.hoist != after.hoist:
            for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                return await guild_log_channel.send(
                    embed = discord.Embed(
                        title= " ",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Role Hoist",
                        value=f"{before.hoist} -> {after.hoist}",
                    ).set_footer(
                        text=f"Role ID: {after.id}"
                    )
                )

        if before.mentionable != after.mentionable:
            for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                return await guild_log_channel.send(
                    embed = discord.Embed(
                        title= " ",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Role Mentionable",
                        value=f"{before.mentionable} -> {after.mentionable}",
                    ).set_footer(
                        text=f"Role ID: {after.id}"
                    )
                )

async def setup(bot):
    await bot.add_cog(OnGuildRoleUpdate(bot))