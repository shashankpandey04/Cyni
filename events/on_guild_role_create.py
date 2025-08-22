import discord
from cyni import premium_check_fun
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
            premium_status = await premium_check_fun(self.bot, role.guild)
            if premium_status in [True] and self.bot.is_premium == False:
                return
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
                embed = generate_embed(
                    guild,
                    title="Role Created",
                    category="logging",
                    description=f"{entry.user.mention} created {role.name} on {created_at}",
                    footer=f"Role ID: {role.id}",
                    fields=[
                        {"name": "Role Name", "value": role.name, "inline": True},
                        {"name": "Role Color", "value": str(role.color), "inline": True},
                        {"name": "Role Permissions", "value": ", ".join([perm for perm, value in role.permissions if value]), "inline": False}
                    ]
                )
                logger = self.bot.get_cog("ThrottledLogger")
                await logger.log_embed(guild_log_channel, embed)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error in on_guild_role_create: {e}")

async def setup(bot):
    await bot.add_cog(OnGuildRoleCreate(bot))