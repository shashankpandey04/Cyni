import mysql.connector
from discord.ext import commands
from db import mycon as db
dev_role_id = 1152951022885535804

class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} loaded cog: Premium Staff Command')

    @commands.command()
    async def set_premium(self,ctx, value: bool):
        try:
            cursor = db.cursor()
            dev_users = [member.name for member in ctx.guild.get_role(dev_role_id).members]
            if ctx.author.name in dev_users:
                server_id = ctx.guild.id
                query = "UPDATE server_config SET premium = %s WHERE guild_id = %s"
                cursor.execute(query, (value, server_id))
                db.commit()
                await ctx.send(f"Premium status set to {value} for this server.")
            else:
                await ctx.send("You are not authorized to use this command.")
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            await ctx.send("An error occurred while trying to set premium status.")
        finally:
            cursor.close()


async def setup(bot):
   await bot.add_cog(Premium(bot))