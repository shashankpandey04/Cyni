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
        guild_log_channel = guild.get_channel(sett.get("moderation_module", {}).get("audit_log"))
        if not guild_log_channel:
            return
        created_at = discord_time(datetime.datetime.now())

        webhooks = await guild_log_channel.webhooks()
        cyni_webhook = None
        for webhook in webhooks:
            if webhook.name == "Cyni":
                cyni_webhook = webhook
            break
        
        if not cyni_webhook:
            bot_avatar = await self.bot.user.avatar.read()
            try:
                cyni_webhook = await guild_log_channel.create_webhook(name="Cyni", avatar=bot_avatar)
            except discord.HTTPException:
                cyni_webhook = None

        if before.name != after.name:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
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
                if cyni_webhook:
                    await cyni_webhook.send(embed=embed)
                else:
                    await guild_log_channel.send(embed=embed)

        if before.category != after.category:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
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
                if cyni_webhook:
                    await cyni_webhook.send(embed=embed)
                else:
                    await guild_log_channel.send(embed=embed)

        if before.is_nsfw() != after.is_nsfw():
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
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
                if cyni_webhook:
                    await cyni_webhook.send(embed=embed)
                else:
                    await guild_log_channel.send(embed=embed)

        changes = []
        if before.overwrites != after.overwrites:
            changes = compare_overwrites(before.overwrites, after.overwrites)
            human_readable_changes = "\n".join([f"{perm[0].replace('_', ' ').title()}: {perm[1].strip()}" for perm in changes])
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.overwrite_update):
                embed = discord.Embed(
                    title= " ",
                    description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                    color=YELLOW_COLOR
                ).add_field(
                    name="Channel Name",
                    value=f"{before.name}",
                ).add_field(
                    name="Overwrites",
                    value=f"{human_readable_changes}",
                ).set_footer(
                    text=f"Channel ID: {after.id}"
                )
                if cyni_webhook:
                    await cyni_webhook.send(embed=embed)
                else:
                    await guild_log_channel.send(embed=embed)


        if before.type != after.type:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
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
                if cyni_webhook:
                    await cyni_webhook.send(embed=embed)
                else:
                    await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnGuildChannelUpdate(bot))