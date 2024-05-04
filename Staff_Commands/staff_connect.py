import discord
from discord.ext import commands

cyni_support_role_id = 1158043149424398406
support_role_id = 1187279080417136651
senior_support_role_id = 1187279102437232710
dev_role_id = 1152951022885535804
management_role_id = 1200642991556145192
qa_team = 1211064601051930634
trial_dev = 1213765319793836032
from db import mycon as mydb

class StaffConnect(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} loaded cog: Staff Connect')

    @commands.command()
    async def staff_sync(self,ctx, target_user: discord.Member = None):
        try:
            mycursor = mydb.cursor()
            target_user = target_user or ctx.author
            if any(role.id in [cyni_support_role_id, qa_team, support_role_id, senior_support_role_id, dev_role_id, management_role_id] for role in ctx.author.roles):
                user_flags = []
                if qa_team in [role.id for role in target_user.roles]:
                    user_flags.append("Cyni QA Team")
                if cyni_support_role_id in [role.id for role in target_user.roles]:
                    user_flags.append("Cyni Team")
                if support_role_id in [role.id for role in target_user.roles]:
                    user_flags.append("Cyni Support")
                if senior_support_role_id in [role.id for role in target_user.roles]:
                    user_flags.append("Cyni Senior Support")
                if management_role_id in [role.id for role in target_user.roles]:
                    user_flags.append("Cyni Management")
                if trial_dev in [role.id for role in target_user.roles]:
                    user_flags.append("Cyni Trial Developer")
                if dev_role_id in [role.id for role in target_user.roles]:
                    user_flags.append("Cyni Developer")
                if ctx.guild.owner_id == target_user.id:
                    user_flags.append("Cyni Owner")
                if not user_flags:
                    await ctx.send(f"{target_user.mention} doesn't have any staff roles. No changes were made.")
                    return
                flags_text = '\n'.join(user_flags)
                sql = "INSERT INTO staff (user_id, flags) VALUES (%s, %s) ON DUPLICATE KEY UPDATE flags = %s"
                val = (target_user.id, flags_text, flags_text)
                mycursor.execute(sql, val)
                mydb.commit()
                embed = discord.Embed(title="Staff Sync", description=f"Staff flags for {target_user.mention} have been updated.",color=0x2F3136)
                await ctx.send(embed=embed)
            else:
                await ctx.send("You don't have the required roles to use this command.")
        except Exception as e:
            print(f"Error: {e}")
            await ctx.send("An error occurred while trying to sync staff roles.")
        finally:
            mycursor.close()

async def setup(bot):
   await bot.add_cog(StaffConnect(bot))