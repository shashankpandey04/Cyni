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
        guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])
        created_at = discord_time(datetime.datetime.now())
        if before.nick != after.nick:
            await guild_log_channel.send(
                embed = discord.Embed(
                    title= " ",
                    description=f"{before.mention} changed their nickname on {created_at}",
                    color=YELLOW_COLOR
                ).set_author(
                    name=after,
                    icon_url=before.avatar.url
                ).set_footer(
                    text=f"User ID: {before.id}"
                ).add_field(
                    name="Before",
                    value=f"{before.nick}",
                ).add_field(
                    name="After",
                    value=f"{after.nick}",
                )
            )
        if before.roles != after.roles:
            role_added = [role for role in after.roles if role not in before.roles]
            role_removed = [role for role in before.roles if role not in after.roles]
            if role_added:
                role_added = [role.mention for role in role_added]
                await guild_log_channel.send(
                    embed = discord.Embed(
                        title= " ",
                        description=f"{before.mention} was given the following roles: {', '.join(role_added)} on {created_at}",
                        color=YELLOW_COLOR
                    ).set_author(
                        name=before,
                        icon_url=before.avatar.url
                    ).set_footer(
                        text=f"User ID: {before.id}"
                    )
                )
            if role_removed:
                role_removed = [role.mention for role in role_removed]
                await guild_log_channel.send(
                    embed = discord.Embed(
                        title= " ",
                        description=f"{before.mention} was removed from the following roles: {', '.join(role_removed)} on {created_at}",
                        color=YELLOW_COLOR
                    ).set_author(
                        name=before,
                        icon_url=before.avatar.url
                    ).set_footer(
                        text=f"User ID: {before.id}"
                    )
                )

async def setup(bot):
    await bot.add_cog(OnMemberUpdate(bot))