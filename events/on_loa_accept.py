import discord
from discord.ext import commands

from utils.constants import GREEN_COLOR

class OnLOAAccept(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_loa_accept(self, loa_doc: dict):
        guild = self.bot.get_guild(loa_doc["guild_id"])
        try:
            user = await guild.fetch_member(int(loa_doc["user_id"]))
        except:
            return
        try:
            await user.send(
                embed=discord.Embed(
                    title=f"Activity Notice Accepted | {guild.name}",
                    description=f"Your {loa_doc['type']} request in **{guild.name}** was accepted!",
                    color=GREEN_COLOR,
                )
            )
        except:
            print(f"Could not DM {user} about accepted LOA in {guild}")

        settings = await self.bot.get_guild_settings(guild.id)
        if settings is None:
            return
        
        loa_module = settings.get("leave_of_absence", {})
        role_ids = loa_module.get("loa_role", 0)
        
        if 0 == role_ids:
            return
        
        loa_role = guild.get_role(role_ids)
        if loa_role is None:
            return
        
        await user.add_roles(loa_role, reason="LOA Accepted")

async def setup(bot):
    await bot.add_cog(OnLOAAccept(bot))