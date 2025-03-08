import discord
import time
from discord.ext import commands

from utils.constants import GREEN_COLOR
from utils.utils import discord_time
import datetime

class OnMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        This event is triggered when a member joins a guild.
        :param member (discord.Member): The member that joined the guild.
        """

        if member.guild.id == 1152949579407442050:
            channel = self.bot.get_channel(1152949580091097131)
            await channel.send(f"<:blobcatfood:1239950637790396446> | 👋 Hey {member.mention}, welcome to the Cyni Systems! You are the `{len(member.guild.members)}th` member!")
            role = member.guild.get_role(1152952489692377148)
            await member.add_roles(role)
        
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

        joined_at = discord_time(datetime.datetime.now())
        embed = discord.Embed(
                title= " ",
                description=f"{member.mention} joined the server on {joined_at}",
                color=GREEN_COLOR
            ).add_field(
                name="Account Created",
                value=f"{discord_time(member.created_at)}",
            ).add_field(
                name="Member Count",
                value=f"{guild.member_count}",
            ).set_footer(
                text=f"User ID: {member.id}"
            )
        try:
            embed.set_thumbnail(
                url=member.avatar.url
            )
        except:
            pass
        #if cyni_webhook:
        #    await cyni_webhook.send(embed=embed)
        #else:
        await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnMemberJoin(bot))