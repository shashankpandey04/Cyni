import os
import discord
from discord.ext import commands
from utils.constants import RED_COLOR
from utils.utils import discord_time, generate_embed
import datetime
from cyni import premium_check_fun

class OnGuildRoleDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_audit_log_entry(self, guild, action=discord.AuditLogAction.role_delete):
        """Get the most recent audit log entry for the specified action."""
        try:
            async for entry in guild.audit_logs(limit=1, action=action):
                return entry
        except discord.Forbidden:
            return None
        return None

    async def _send_log_embed(self, channel, embed):
        """Send an embed to the log channel with error handling."""
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error sending role delete log: {e}")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """
        This event is triggered when a role is deleted in a guild.
        """
        try:
            guild = role.guild
            premium_status = await premium_check_fun(self.bot, guild)
            if premium_status in ["not_premium_server"]:
                return
            sett = await self.bot.settings.find_by_id(guild.id)
            if not sett:
                return
            
            moderation_module = sett.get("moderation_module", {})
            if not moderation_module.get("enabled", False) or not moderation_module.get("audit_log"):
                return
                
            guild_log_channel = guild.get_channel(moderation_module["audit_log"])
            if not guild_log_channel:
                return
            
            audit_entry = await self._get_audit_log_entry(guild)
            created_at = discord_time(datetime.datetime.now())
            
            user_mention = audit_entry.user.mention if audit_entry else "System"

            embed = generate_embed(
                guild,
                title="Role Deleted",
                category="logging",
                description=f"{user_mention} deleted **{role.name}** on {created_at}",
                footer=f"Role ID: {role.id}",
                fields=[
                    {"name": "Role Color", "value": str(role.color), "inline": True},
                    {"name": "Role Position", "value": str(role.position), "inline": True},
                    {"name": "Members", "value": len(role.members), "inline": True}
                ]
            )
            if role.members and (await self.bot.premium.find_by_id(guild.id)) and self.bot.is_premium:
                members_list = "\n".join([member.mention for member in role.members])
                with open(f"{role.name}_deleted_members.txt", "w") as file:
                    file.write(members_list)
                with open(f"{role.name}_deleted_members.txt", "rb") as file:
                    await guild_log_channel.send(
                        content=f"The following members were affected by the deletion of {role.name}:",
                        file=discord.File(file, filename=f"{role.name}_deleted_members.txt")
                    )
                    os.remove(f"{role.name}_deleted_members.txt")

            await self._send_log_embed(guild_log_channel, embed)
            
        except Exception as e:
            print(f"Error in on_guild_role_delete: {e}")

async def setup(bot):
    await bot.add_cog(OnGuildRoleDelete(bot))