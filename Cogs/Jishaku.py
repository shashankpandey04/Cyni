import discord
import jishaku
from discord.ext import commands
from jishaku.codeblocks import codeblock_converter, Codeblock
from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES
from jishaku.features.baseclass import Feature

OWNER = 1201129677457215558
LOGGING_CHANNEL = 1257705346525560885


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

async def setup(bot):
    await bot.add_cog(CustomDebugCog(bot=bot))