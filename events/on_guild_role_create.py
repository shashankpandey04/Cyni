import discord
import time
from discord.ext import commands

from utils.constants import RED_COLOR
from utils.utils import discord_time
import datetime

class OnGuildRoleCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """
        This event is triggered when a role is created in a guild.
        :param role (discord.Role): The role that was created.
        """
        
        sett = await self.bot.settings.find_by_id(role.guild.id)
        guild = role.guild
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
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

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
            embed = discord.Embed(
                    title= " ",
                    description=f"{entry.user.mention} created {role.mention} on {created_at}",
                    color=RED_COLOR
                ).set_footer(
                    text=f"Role ID: {role.id}"
                )
            if cyni_webhook:
                await cyni_webhook.send(embed=embed)
            else:
                await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnGuildRoleCreate(bot))