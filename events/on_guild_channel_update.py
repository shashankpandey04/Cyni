import discord
import time
from discord.ext import commands
from utils.utils import compare_overwrites

from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
import datetime

class OnGuildChannelUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """
        This event is triggered when a channel is updated in a guild.
        :param before (discord.TextChannel): The channel before the update.
        :param after (discord.TextChannel): The channel after the update.
        """
        
        sett = await self.bot.settings.find_by_id(before.guild.id)
        guild = before.guild
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
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                return await guild_log_channel.send(
                    embed = discord.Embed(
                        title= " ",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Channel Name",
                        value=f"{before.name} -> {after.name}",
                    ).add_field(
                        name="Channel Category",
                        value=f"{before.category}",
                    ).set_footer(
                        text=f"Channel ID: {after.id}"
                    )
                )

        if before.category != after.category:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                return await guild_log_channel.send(
                    embed = discord.Embed(
                        title= " ",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Channel Name",
                        value=f"{before.name}",
                    ).add_field(
                        name="Channel Category",
                        value=f"{before.category} -> {after.category}",
                    ).set_footer(
                        text=f"Channel ID: {after.id}"
                    )
                )

        if before.is_nsfw() != after.is_nsfw():
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                return await guild_log_channel.send(
                    embed = discord.Embed(
                        title= " ",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Channel Name",
                        value=f"{before.name}",
                    ).add_field(
                        name="Channel NSFW",
                        value=f"{before.is_nsfw()} -> {after.is_nsfw()}",
                    ).set_footer(
                        text=f"Channel ID: {after.id}"
                    )
                )

        changes = []
        if before.overwrites != after.overwrites:
            changes = compare_overwrites(before.overwrites, after.overwrites)
            if changes:
                if len(changes) > 1024:
                    changes = changes[:1021] + "..."
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.overwrite_update):
                    return await guild_log_channel.send(
                        embed = discord.Embed(
                            title= " ",
                            description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                            color=YELLOW_COLOR
                        ).add_field(
                            name="Channel Name",
                            value=f"{before.name}",
                        ).add_field(
                            name="Overwrites",
                            value=f"{changes}",
                        ).set_footer(
                            text=f"Channel ID: {after.id}"
                        )
                    )


        if before.type != after.type:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                return await guild_log_channel.send(
                    embed = discord.Embed(
                        title= " ",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Channel Name",
                        value=f"{before.name}",
                    ).add_field(
                        name="Channel Type",
                        value=f"{before.type} -> {after.type}",
                    ).set_footer(
                        text=f"Channel ID: {after.id}"
                    )
                )

async def setup(bot):
    await bot.add_cog(OnGuildChannelUpdate(bot))