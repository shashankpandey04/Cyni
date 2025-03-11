import discord
from discord.ext import commands

from utils.constants import BLANK_COLOR, GREEN_COLOR


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
            pass

        settings = await self.bot.get_guild_settings(guild.id)
        if settings is None:
            return
        
        loa_module = settings.get("leave_of_absence", {})
        role_ids = loa_module.get("role_ids", [])
        
        loa_roles = list(
            filter(
                lambda x: x is not None,
                [
                    discord.utils.get(guild.roles, id=identifier)
                    for identifier in role_ids
                ],
            )
        )
        for rl in loa_roles:
            if rl not in user.roles:
                try:
                    await user.add_roles(rl)
                except discord.HTTPException:
                    pass

async def setup(bot):
    await bot.add_cog(OnLOAAccept(bot))