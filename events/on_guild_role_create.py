import discord
import time
from discord.ext import commands

from utils.constants import RED_COLOR
from utils.utils import discord_time, generate_embed
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
        try:
            sett = await self.bot.settings.find_by_id(role.guild.id)
            if not (await self.bot.premium.find_by_id(role.guild.id)) or not self.bot.is_premium:
                return
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

            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                embed = await generate_embed(
                    guild.id,
                    title="Role Created",
                    category="logging",
                    description=f"{entry.user.mention} created {role.mention} on {created_at}",
                    footer=f"Role ID: {role.id}",
                )
                await guild_log_channel.send(embed=embed)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error in on_guild_role_create: {e}")

async def setup(bot):
    await bot.add_cog(OnGuildRoleCreate(bot))