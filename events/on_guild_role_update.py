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
            await guild_log_channel.send(
                embed = discord.Embed(
                    title= " ",
                    description=f"{before.mention} was updated on {created_at}",
                    color=YELLOW_COLOR
                ).add_field(
                    name="Role Name",
                    value=f"{before.name} -> {after.name}",
                ).add_field(
                    name="Role ID",
                    value=f"{before.id}",
                ).set_footer(
                    text=f"Role Position: {before.position}"
                )
            )

        if before.color != after.color:
            await guild_log_channel.send(
                embed = discord.Embed(
                    title= " ",
                    description=f"{before.mention} was updated on {created_at}",
                    color=YELLOW_COLOR
                ).add_field(
                    name="Role Color",
                    value=f"{before.color} -> {after.color}",
                ).add_field(
                    name="Role ID",
                    value=f"{before.id}",
                ).set_footer(
                    text=f"Role Position: {before.position}"
                )
            )

        if before.permissions != after.permissions:
            await guild_log_channel.send(
                embed = discord.Embed(
                    title= " ",
                    description=f"{before.mention} was updated on {created_at}",
                    color=YELLOW_COLOR
                ).add_field(
                    name="Role Permissions",
                    value=f"{before.permissions.value} -> {after.permissions.value}",
                ).add_field(
                    name="Role ID",
                    value=f"{before.id}",
                ).set_footer(
                    text=f"Role Position: {before.position}"
                )
            )

        if before.hoist != after.hoist:
            await guild_log_channel.send(
                embed = discord.Embed(
                    title= " ",
                    description=f"{before.mention} was updated on {created_at}",
                    color=YELLOW_COLOR
                ).add_field(
                    name="Role Hoist",
                    value=f"{before.hoist} -> {after.hoist}",
                ).add_field(
                    name="Role ID",
                    value=f"{before.id}",
                ).set_footer(
                    text=f"Role Position: {before.position}"
                )
            )

        if before.mentionable != after.mentionable:
            await guild_log_channel.send(
                embed = discord.Embed(
                    title= " ",
                    description=f"{before.mention} was updated on {created_at}",
                    color=YELLOW_COLOR
                ).add_field(
                    name="Role Mentionable",
                    value=f"{before.mentionable} -> {after.mentionable}",
                ).add_field(
                    name="Role ID",
                    value=f"{before.id}",
                ).set_footer(
                    text=f"Role Position: {before.position}"
                )
            )

async def setup(bot):
    await bot.add_cog(OnGuildRoleUpdate(bot))