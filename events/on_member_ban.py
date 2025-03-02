import discord
import time
from discord.ext import commands

from utils.constants import RED_COLOR
from utils.utils import discord_time
import datetime

class OnMemberBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """
        This event is triggered when a member is banned from a guild.
        :param guild (discord.Guild): The guild where the member was banned.
        :param user (discord.User): The user that was banned.
        """
        
        sett = await self.bot.settings.find_by_id(guild.id)
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
            return
        guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])

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
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            embed = discord.Embed(
                    title= " ",
                    description=f"{entry.user.mention} banned {user.mention}\nUser was banned {created_at}",
                    color=RED_COLOR
                ).set_footer(
                    text=f"User ID: {user.id}"
                ).set_thumbnail(
                    url=user.avatar.url
                )
            if cyni_webhook:
                await cyni_webhook.send(embed=embed)
            else:
                await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnMemberBan(bot))