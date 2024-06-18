import discord
from discord.ext import commands
from menu import SupportBtn

class Help(commands.Cog):
    def __init__ (self,bot):
        self.bot = bot

    @commands.hybrid_command(name="help", aliases=["h","support"], brief="Get help with Cyni", description="Get help with Cyni and find useful links.", usage="help", help="Get help with Cyni and find useful links.")
    async def support(self,ctx):
        embed = discord.Embed(title="Cyni Help",color=0x00FF00)
        embed.add_field(name="Cyni Docs",value="[Cyni Docs](https://qupr-digital.gitbook.io/cyni-docs/)",inline=False)
        embed.add_field(name="Support Server",value="[Join Cyni Support Server for help.](https://discord.gg/J96XEbGNDm)",inline=False)
        embed.add_field(name="Status Page", value="[CyberWorks Status](https://cyberworks.statuspage.io/)", inline=False)
        await ctx.channel.send(embed=embed,view = SupportBtn())

async def setup(bot):
    await bot.add_cog(Help(bot))
