import mysql.connector
from discord.ext import commands

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="cyni"
)
cursor = db.cursor()

dev_role_id = 1152951022885535804

class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} loaded cog: Premium Staff Command')

    @commands.command()
    async def set_premium(self,ctx, guild: int, status: str):
        try:
            if any(role.id in [dev_role_id] for role in ctx.author.roles):
                status = status.lower()  # Convert to lowercase for case-insensitivity
                if status in ['true', 'yes', 'on', '1']:
                    premium_value = 1
                elif status in ['false', 'no', 'off', '0']:
                    premium_value = 0
                else:
                    await ctx.send("Invalid value for status. Please provide 'true' or 'false'.")
                    return    
                cursor = db.cursor()
                cursor.execute("UPDATE server_config SET premium = %s WHERE guild_id = %s", (premium_value, guild))
                db.commit()
                cursor.close()
                await ctx.send(f"Premium status has been set to {status}.")
        except Exception as e:
                await ctx.send(f"An error occurred while setting premium status: {e}")

async def setup(bot):
   await bot.add_cog(Premium(bot))