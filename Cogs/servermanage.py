import discord
from discord.ext import commands
from cyni import on_command_error
from menu import SetupView

class ServerManage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="servermanage",aliases=["config"])
    async def servermanage(self,ctx):
        '''Manage Your Server with Cyni'''
        try:
            if ctx.author.guild_permissions.administrator:
                embed = discord.Embed(title="Server Manage",description='''
                                    **Staff Roles:**
                                    - *Discord Staff Roles:* These roles grant permission to use Cyni's moderation commands.\n
                                    - *Management Roles:* Users with these roles can utilize Cyni's management commands, including Application Result commands, Staff Promo/Demo command, and setting the Moderation Log channel.

                                    **Server Config:**
                                    - Easily view and edit your server configuration settings.

                                    **Anti-ping Module:**
                                    - Messages are sent if a user with specific roles attempts to ping anyone. Bypass roles can be configured to allow certain users to ping others with that role.

                                    **Support Server:**
                                    - Need assistance? Join the Cyni Support Server for help.
                                        '''
                                        ,color=0x2F3136) 
                await ctx.send(embed=embed, view=SetupView())
            else:
                await ctx.send("❌ You don't have permission to use this command.")
        except Exception as error:
                await on_command_error(ctx, error)

async def setup(bot):
     await bot.add_cog(ServerManage(bot))