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
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                return await guild_log_channel.send(
                    embed = discord.Embed(
                        title= " ",
                        description=f"{entry.user.mention} updated {before.mention}\n Edited Nickname {created_at}",
                        color=YELLOW_COLOR
                    ).add_field(
                        name="Nickname",
                        value=f"{before.nick} -> {after.nick}",
                    ).set_footer(
                        text=f"User ID: {before.id}"
                    )
                )
                
        if before.roles != after.roles:
            role_added = [role for role in after.roles if role not in before.roles]
            role_removed = [role for role in before.roles if role not in after.roles]
            if role_added:
                role_added = [role.mention for role in role_added]
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    try:
                        return await guild_log_channel.send(
                            embed = discord.Embed(
                                title= " ",
                                description=f"{entry.user.mention} added {', '.join(role_added)} to {before.mention}\n Event Time: {created_at}",
                                color=YELLOW_COLOR
                            ).set_author(
                                name=before,
                            ).set_footer(
                                text=f"User ID: {before.id}"
                            )
                        )
                    except Exception as e:
                        pass
            if role_removed:
                role_removed = [role.mention for role in role_removed]
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    try:
                        return await guild_log_channel.send(
                            embed = discord.Embed(
                                title= " ",
                                description=f"{entry.user.mention} removed {', '.join(role_removed)} from {before.mention}\nEvent Time: {created_at}",
                                color=YELLOW_COLOR
                            ).set_author(
                                name=before,
                            ).set_footer(
                                text=f"User ID: {before.id}"
                            )
                        )
                    except Exception as e:
                        pass

async def setup(bot):
    await bot.add_cog(OnMemberUpdate(bot))