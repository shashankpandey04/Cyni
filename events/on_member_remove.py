import discord
import time
from discord.ext import commands

from utils.constants import RED_COLOR
from utils.utils import discord_time
import datetime

class OnMemberRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """
        This event is triggered when a member leaves a guild.
        :param member (discord.Member): The member that left the guild.
        """
        
        sett = await self.bot.settings.find_by_id(member.guild.id)
        guild = member.guild
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if sett.get("moderation_module", {}).get("audit_log") is None:
            return
        guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])

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

        left_at = discord_time(datetime.datetime.now())
        embed = discord.Embed(
                title= " ",
                description=f"{member.mention} left the server on {left_at}",
                color=RED_COLOR
            ).add_field(
                name="Member Count",
                value=f"{guild.member_count}",
            ).set_author(
                name=member,
                icon_url=member.avatar.url
            ).set_footer(
                text=f"User ID: {member.id}"
            ).set_thumbnail(
                url=member.avatar.url
            )
        #if cyni_webhook:
        #    await cyni_webhook.send(embed=embed)
        #else:
        await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnMemberRemove(bot))