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
        
        # Remove duplicate check and simplify logic
        try:
            if not sett.get("moderation_module", {}).get("enabled") or not sett.get("moderation_module", {}).get("audit_log"):
                return
        except KeyError:
            return
            
        guild_log_channel = guild.get_channel(sett.get("moderation_module", {}).get("audit_log"))
        if not guild_log_channel:
            return
        created_at = discord_time(datetime.datetime.now())

        #webhooks = await guild_log_channel.webhooks()
        #cyni_webhook = None
        #for webhook in webhooks:
        #    if webhook.name == "Cyni":
        #        cyni_webhook = webhook
        #        break
        
        #if not cyni_webhook:
        #    bot_avatar = await self.bot.user.avatar.read()
        #    try:
        #        cyni_webhook = await guild_log_channel.create_webhook(name="Cyni", avatar=bot_avatar)
        #    except discord.HTTPException:
        #        cyni_webhook = None

        if before.name != after.name:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                embed = discord.Embed(
                        title="Channel Name Updated",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Before",
                        value=f"{before.name}",
                        inline=True
                    ).add_field(
                        name="After",
                        value=f"{after.name}",
                        inline=True
                    ).add_field(
                        name="Category",
                        value=f"{before.category}" if before.category else "None",
                        inline=False
                    ).set_footer(
                        text=f"Channel ID: {after.id}"
                    )
                #if cyni_webhook:
                #    await cyni_webhook.send(embed=embed)
                #else:
                await guild_log_channel.send(embed=embed)

        if before.category != after.category:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                embed = discord.Embed(
                        title="Channel Category Updated",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Channel",
                        value=f"{before.name}",
                        inline=False
                    ).add_field(
                        name="Before",
                        value=f"{before.category}" if before.category else "None",
                        inline=True
                    ).add_field(
                        name="After",
                        value=f"{after.category}" if after.category else "None",
                        inline=True
                    ).set_footer(
                        text=f"Channel ID: {after.id}"
                    )
                #if cyni_webhook:
                #    await cyni_webhook.send(embed=embed)
                #else:
                await guild_log_channel.send(embed=embed)

        if before.is_nsfw() != after.is_nsfw():
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                embed = discord.Embed(
                        title="Channel NSFW Setting Updated",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Channel",
                        value=f"{before.name}",
                        inline=False
                    ).add_field(
                        name="Before",
                        value=f"NSFW: {'Enabled' if before.is_nsfw() else 'Disabled'}",
                        inline=True
                    ).add_field(
                        name="After",
                        value=f"NSFW: {'Enabled' if after.is_nsfw() else 'Disabled'}",
                        inline=True
                    ).set_footer(
                        text=f"Channel ID: {after.id}"
                    )
                #if cyni_webhook:
                #    await cyni_webhook.send(embed=embed)
                #else:
                await guild_log_channel.send(embed=embed)

        # Improve the permission overwrite formatting
        if before.overwrites != after.overwrites:
            changes = compare_overwrites(before.overwrites, after.overwrites)
            
            human_readable_changes = []
            for target, perm_type, perm_name, old_value, new_value in changes:
                target_name = target.name if hasattr(target, 'name') else str(target)

                old_symbol = "❌" if old_value is False else "✅" if old_value is True else "➖"
                new_symbol = "❌" if new_value is False else "✅" if new_value is True else "➖"
                readable_name = perm_name.replace('_', ' ').title()
                
                human_readable_changes.append(f"**{target_name}**: {readable_name} ({old_symbol} → {new_symbol})")
            formatted_changes = "\n".join(human_readable_changes) if human_readable_changes else "No detailed permission changes available"
            
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.overwrite_update):
                embed = discord.Embed(
                    title="Channel Permissions Updated",
                    description=f"{entry.user.mention} updated permissions for {before.mention} on {created_at}",
                    color=YELLOW_COLOR
                ).add_field(
                    name="Channel",
                    value=f"{before.name}",
                    inline=False
                ).add_field(
                    name="Permission Changes",
                    value=formatted_changes,
                    inline=False
                ).set_footer(
                    text=f"Channel ID: {after.id}"
                )
                #if cyni_webhook:
                #    await cyni_webhook.send(embed=embed)
                #else:
                await guild_log_channel.send(embed=embed)

        if before.type != after.type:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                embed = discord.Embed(
                        title="Channel Type Updated",
                        description=f"{entry.user.mention} updated {before.mention} on {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Channel",
                        value=f"{before.name}",
                        inline=False
                    ).add_field(
                        name="Before",
                        value=f"{str(before.type).replace('_', ' ').title()}",
                        inline=True
                    ).add_field(
                        name="After",
                        value=f"{str(after.type).replace('_', ' ').title()}",
                        inline=True
                    ).set_footer(
                        text=f"Channel ID: {after.id}"
                    )
                #if cyni_webhook:
                #    await cyni_webhook.send(embed=embed)
                #else:
                await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnGuildChannelUpdate(bot))
