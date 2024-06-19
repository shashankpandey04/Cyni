import discord
from discord.ext import commands
from cyni import on_command_error
from menu import SetupView, display_server_config

class ServerManage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="server",aliases=["config"])
    async def server(self, ctx):
        pass
    
    @server.command(name="manage")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def manage(self,ctx):
        '''Manage Your Server with Cyni'''
        try:
            if ctx.author.guild_permissions.administrator:
                embed = discord.Embed(title="Server Manage",description='',color=0x2F3136)
                embed.add_field(name="Basic Configuration",
                                value="""
                                > Setup your Staff & Management Roles to use Cyni.
                                """
                                ,inline=False)
                embed.add_field(name="Anti-Ping",
                                value="""
                                > What is Anti-Ping? Anti-Ping is a feature that allows you to prevent users from pinging specific roles.
                                """
                                ,inline=False)
                embed.add_field(name="Staff Management Channel",
                                value="""
                                > Set the channel where staff management commands will be logged. Like promotions, demotions, applications, etc.
                                """
                                ,inline=False)
                embed.add_field(name="Message Quota",
                                value="""
                                > Message Quota: Set the message quota for your server.
                                """
                                ,inline=False)
                await ctx.send(embed=embed, view=SetupView())
            else:
                await ctx.send("❌ You don't have permission to use this command.")
        except Exception as error:
                await on_command_error(ctx, error)

    @server.command(name="config")
    async def config(self,ctx):
         '''View Server Configuration'''
         await display_server_config(ctx)
         
async def setup(bot):
     await bot.add_cog(ServerManage(bot))
