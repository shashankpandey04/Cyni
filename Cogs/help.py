import discord
from discord.ext import commands
from menu import SupportBtn

class Help(commands.Cog):
    def __init__ (self,bot):
        self.bot = bot

    @commands.command()
    async def help(self,ctx):
        embed = discord.Embed(title="Cyni Help",color=0x00FF00)
        embed.add_field(name="Cyni Docs",value="[Cyni Docs](https://qupr-digital.gitbook.io/cyni-docs/)",inline=False)
        embed.add_field(name="Support Server",value="[Join Cyni Support Server for help.](https://discord.gg/2D29TSfNW6)",inline=False)
        await ctx.channel.send(embed=embed,view = SupportBtn())

    @commands.command()
    async def support(self,ctx):
        embed = discord.Embed(title="Cyni Help",color=0x00FF00)
        embed.add_field(name="Cyni Docs",value="[Cyni Docs](https://qupr-digital.gitbook.io/cyni-docs/)",inline=False)
        embed.add_field(name="Support Server",value="[Join Cyni Support Server for help.](https://discord.gg/2D29TSfNW6)",inline=False)
        await ctx.channel.send(embed=embed,view = SupportBtn())

async def setup(bot):
    await bot.add_cog(Help(bot))