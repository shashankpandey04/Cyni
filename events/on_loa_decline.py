import discord
from discord.ext import commands

from utils.constants import RED_COLOR


class OnLOADecline(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_loa_decline(self, loa_doc: dict):
        """
        Event triggered when an LOA request is declined.

        Parameters:
        -----------
        loa_doc: dict
            The LOA document containing details about the request
        """
        try:
            # Validate document data
            if not loa_doc.get("guild_id") or not loa_doc.get("user_id") or not loa_doc.get("type"):
                self.bot.logger.warning(f"Incomplete LOA document received: {loa_doc}")
                return

            # Get guild
            guild = self.bot.get_guild(loa_doc["guild_id"])
            if not guild:
                self.bot.logger.warning(f"Could not find guild with ID {loa_doc['guild_id']}")
                return

            # Get user
            try:
                user = await guild.fetch_member(int(loa_doc["user_id"]))
            except discord.errors.NotFound:
                self.bot.logger.info(f"User {loa_doc['user_id']} not found in guild {guild.name}")
                return
            except discord.errors.HTTPException as e:
                self.bot.logger.error(f"HTTP error while fetching member: {str(e)}")
                return

            # Send DM notification
            try:
                embed = discord.Embed(
                    title=f"Activity Notice Declined | {guild.name}",
                    description=f"Your {loa_doc['type']} request in **{guild.name}** was declined.",
                    color=RED_COLOR,
                )
                
                if loa_doc.get("reason"):
                    embed.add_field(name="Reason", value=loa_doc["reason"])
                    
                await user.send(embed=embed)
                self.bot.logger.info(f"LOA decline notification sent to {user} in {guild.name}")
                
            except discord.errors.Forbidden:
                self.bot.logger.info(f"Could not send LOA decline DM to {user} - DMs disabled")
                
        except Exception as e:
            self.bot.logger.error(f"Error in on_loa_decline event: {str(e)}")


async def setup(bot):
    await bot.add_cog(OnLOADecline(bot))