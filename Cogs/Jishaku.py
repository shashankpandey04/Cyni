import discord
import jishaku
from discord.ext import commands
from jishaku.codeblocks import codeblock_converter, Codeblock
from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES
from jishaku.features.baseclass import Feature
import requests

OWNER = 1201129677457215558
LOGGING_CHANNEL = 1257705346525560885

REGULAR_DEPLOMENT_LINK = "http://31.97.62.69:3000/api/deploy/1aaa5f61e1137efaf565a24027c8650d7b328e09bf4d11b3"
PREMIUM_DEPLOYMENT_LINK = "http://31.97.62.69:3000/api/deploy/15153e21ebf9dc35994bc5e850a437cc0903bf2dc76cd355"

class CustomDebugCog(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    """
    Custom Jishaku Cog for command logging
    """

    @Feature.Command(parent="jsk", name="creator")
    async def jsk_creator(self, ctx: commands.Context):
        try:
            owner = await ctx.guild.fetch_member(OWNER)
        except discord.NotFound:
            owner = None

        if owner is None:
            return await ctx.send(
                f"The creator of {self.bot.user.mention} is <@{OWNER}>"
            )

        embed = discord.Embed(
            title=f"{owner.name}#{owner.discriminator}", color=0x2A2D31
        )
        embed.add_field(
            name=f"Owner of {self.bot.user.name}",
            value=f"{owner.mention}",
            inline=False,
        )
        embed.add_field(name="ID", value=f"{owner.id}", inline=False)
        embed.set_footer(
            text=f"{owner.name}#{owner.discriminator} is the owner of {self.bot.user.name}",
            icon_url=ctx.guild.icon,
        )
        embed.set_thumbnail(url=owner.display_avatar.url)
        await ctx.send(embed=embed)

    @Feature.Command(parent="jsk", name="restart")
    async def jsk_restart(self, ctx: commands.Context):
        """Restart the bot."""
        if ctx.author.id != OWNER:
            return await ctx.send("You do not have permission to use this command.")

        if self.bot.is_premium:
            deploy_link = PREMIUM_DEPLOYMENT_LINK
        else:
            deploy_link = REGULAR_DEPLOMENT_LINK
        try:
            response = requests.get(deploy_link)
            if response.status_code == 200:
                await ctx.send("Bot is restarting...")
            else:
                await ctx.send(f"Failed to restart the bot. Status code: {response.status_code}")
        except Exception as e:
            await ctx.send(f"An error occurred while trying to restart the bot: {e}")
            self.bot.logger.error(f"Failed to restart bot: {e}")

async def setup(bot):
    await bot.add_cog(CustomDebugCog(bot=bot))