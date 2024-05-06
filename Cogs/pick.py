import discord
from discord.ext import commands
from cyni import on_command_error
import random

class Pick(commands.Cog):
    def __init__(self,bot):
        self.bot = bot;

    @commands.hybrid_command(name="pick",aliases=["choose"])
    async def pick(self,ctx,option1: str,option2: str):
        '''Pick between two options'''
        try:
            option = random.choice([option1, option2])
            await ctx.send(f"I pick {option}")
        except Exception as error:
                await on_command_error(ctx, error)

async def setup(bot):
     await bot.add_cog(Pick(bot))