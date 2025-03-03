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
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
            return
        guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])
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
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
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
                if cyni_webhook:
                    await cyni_webhook.send(embed=embed)
                else:
                    await guild_log_channel.send(embed=embed)

        if before.color != after.color:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
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
                if cyni_webhook:
                    await cyni_webhook.send(embed=embed)
                else:
                    await guild_log_channel.send(embed=embed)

        if before.permissions != after.permissions:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                before_perms = [perm for perm, value in before.permissions if value]
                after_perms = [perm for perm, value in after.permissions if value]
                added_perms = set(after_perms) - set(before_perms)
                removed_perms = set(before_perms) - set(after_perms)
                
                embed = discord.Embed(
                        title= "Role Permissions Update",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Added Permissions",
                        value=", ".join(added_perms) if added_perms else "None",
                    ).add_field(
                        name="Removed Permissions",
                        value=", ".join(removed_perms) if removed_perms else "None",
                    ).set_footer(
                        text=f"Role ID: {after.id}"
                    )
                if cyni_webhook:
                    await cyni_webhook.send(embed=embed)
                else:
                    await guild_log_channel.send(embed=embed)

        if before.hoist != after.hoist:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
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
                if cyni_webhook:
                    await cyni_webhook.send(embed=embed)
                else:
                    await guild_log_channel.send(embed=embed)

        if before.mentionable != after.mentionable:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
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
                if cyni_webhook:
                    await cyni_webhook.send(embed=embed)
                else:
                    await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnGuildRoleUpdate(bot))