import discord
from discord.ext import commands
from cyni import on_command_error

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="avatar", aliases=["av"])
    async def avatar(self, ctx, user: discord.User = None):  # Use discord.User instead of discord.user
        try:
            if user is None:
                user = ctx.author
            embed = discord.Embed(title=f"{user.name}'s Avatar", color=0x2F3136)
            embed.set_image(url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        except Exception as error:
            await on_command_error(ctx, error)

async def setup(bot):
    await bot.add_cog(Avatar(bot))
