import discord
import time
from discord.ext import commands

from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
import datetime

class OnMessageEdit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """
        This event is triggered when a message is edited.
        :param before (discord.Message): The message before it was edited.
        :param after (discord.Message): The message after it was edited.
        """
        
        if before.author.bot:
            return
        if before.content == after.content:
            return
        sett = await self.bot.settings.find_by_id(before.guild.id)
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
            return
        if not sett.get("moderation_module", {}).get("audit_log"):
            return
        guild_log_channel = before.guild.get_channel(sett["moderation_module"]["audit_log"])

        webhooks = await guild_log_channel.webhooks()
        cyni_webhook = None
        for webhook in webhooks:
            if webhook.name == "Cyni":
                cyni_webhook = webhook
            break
        
        if not cyni_webhook:
            bot_avatar = await self.bot.user.avatar.read()
            cyni_webhook = await guild_log_channel.create_webhook(name="Cyni", avatar=bot_avatar)

        created_at = discord_time(datetime.datetime.now())
        if len(before.content) > 1024:
            before.content = before.content[:1021] + "..."
        if len(after.content) > 1024:
            after.content = after.content[:1021] + "..."
        embed = discord.Embed(
                title= " ",
                description=f"Message by {before.author.mention} edited {created_at}",
                color=YELLOW_COLOR
            ).add_field(
                name="Before",
                value=f"{before.content}",
            ).add_field(
                name="After",
                value=f"{after.content}",
            ).set_footer(
                text=f"Message ID: {before.id}"
            )
        if cyni_webhook:
            await cyni_webhook.send(embed=embed)
        else:
            await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnMessageEdit(bot))