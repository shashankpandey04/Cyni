import discord
import time
from discord.ext import commands

from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
import datetime

class OnMemberUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """
        This event is triggered when a member's information is updated.
        :param before (discord.Member): The member's information before the update.
        :param after (discord.Member): The member's information after the update.
        """

        sett = await self.bot.settings.find_by_id(before.guild.id)
        guild = before.guild
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
                return
        guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])
        if not guild_log_channel:
            return

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

        created_at = discord_time(datetime.datetime.now())
        if before.nick != after.nick:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                embed = discord.Embed(
                        description=f"{entry.user.mention} updated {before.mention}\n Edited Nickname {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Nickname",
                        value=f"{before.nick} -> {after.nick}",
                    ).set_footer(
                        text=f"User ID: {before.id}"
                    )
                if cyni_webhook:
                    await cyni_webhook.send(embed=embed)
                else:
                    await guild_log_channel.send(embed=embed)
                
        if before.roles != after.roles:
            role_added = [role for role in after.roles if role not in before.roles]
            role_removed = [role for role in before.roles if role not in after.roles]
            if role_added:
                role_added = [role.mention for role in role_added]
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    embed = discord.Embed(
                        description=f"{entry.user.mention} added {', '.join(role_added)} to {before.mention}\n {created_at}",
                        color=YELLOW_COLOR
                        ).set_author(
                            name=before,
                        ).set_footer(
                            text=f"User ID: {before.id}"
                        )
                    if cyni_webhook:
                        await cyni_webhook.send(embed=embed)
                    else:
                        await guild_log_channel.send(embed=embed)
                    
            if role_removed:
                role_removed = [role.mention for role in role_removed]
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    embed = discord.Embed(
                            description=f"{entry.user.mention} removed {', '.join(role_removed)} from {before.mention}\nEvent Time: {created_at}",
                            color=YELLOW_COLOR
                        ).set_author(
                            name=before,
                        ).set_footer(
                            text=f"User ID: {before.id}"
                        )
                    if cyni_webhook:
                        await cyni_webhook.send(embed=embed)
                    else:
                        await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnMemberUpdate(bot))