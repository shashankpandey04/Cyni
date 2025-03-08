import discord
from discord.ext import commands

from utils.constants import RED_COLOR, GREEN_COLOR
from utils.utils import discord_time
import datetime

class OnGuildChannelCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """
        This event is triggered when a channel is created in a guild.
        :param channel (discord.TextChannel): The channel that was created.
        """
        
        sett = await self.bot.settings.find_by_id(channel.guild.id)
        guild = channel.guild
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

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
            embed = discord.Embed(
                description=f"{entry.user.mention} created {channel.mention} on {created_at}",
                color=GREEN_COLOR
            ).set_footer(
                text=f"Channel ID: {channel.id}"
            )
            #if cyni_webhook:
            #    await cyni_webhook.send(embed=embed)
            #else:
            await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnGuildChannelCreate(bot))