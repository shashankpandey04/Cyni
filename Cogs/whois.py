import discord
from discord.ext import commands
from db import mycon as mydb

class Whois(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} loaded cog: Whois')

    @commands.hybrid_command(name="whois", aliases=["userinfo","w"], brief="Get user information", description="Get information about a user in the server.", usage="whois [user]", help="Get information about a user in the server. If no user is specified, the bot will return information about the command author.")
    async def whois(self, ctx, *, user_info=None):
        try:
            mycursor = mydb.cursor()
            if user_info is None:
                member = ctx.author
            else:
                if user_info.startswith('<@') and user_info.endswith('>'):
                    user_id = int(user_info[2:-1])
                    member = ctx.guild.get_member(user_id)
                else:
                    member = discord.utils.find(lambda m: m.name == user_info, ctx.guild.members)
            if member:
                support_server_id = 1152949579407442050
                support_server = self.bot.get_guild(support_server_id)
                user_emoji = discord.utils.get(support_server.emojis, id=1191057214727786598)
                cyni_emoji = discord.utils.get(support_server.emojis, id=1210274111956324444)
                discord_emoji = discord.utils.get(support_server.emojis, id=1215565113663430696)
                
                # Fetch staff data from MySQL
                sql = "SELECT flags FROM staff WHERE user_id = %s"
                val = (member.id,)
                mycursor.execute(sql, val)
                result = mycursor.fetchone()
                if result:
                    staff_flags = result[0]
                else:
                    staff_flags = ""

                embed = discord.Embed(title="User Information", color=member.color)
                hypesquad_flags = member.public_flags
                hypesquad_values = [str(flag).replace("UserFlags.", "").replace("_", " ").title() for flag in hypesquad_flags.all()]
                if hypesquad_values:
                    hypesquad_text = "\n".join(hypesquad_values)
                    embed.add_field(name=f"{discord_emoji} Discord Flags", value=f"{hypesquad_text}", inline=True)
                user_flags = staff_flags.replace("{cyni_emoji}", "")
                user_flags = [flag.strip() for flag in user_flags.split("\n") if flag.strip()]
                if user_flags:
                    staff_text = "\n".join(user_flags)
                    embed.add_field(name=f'{cyni_emoji} Staff Flags', value=f" {staff_text}", inline=True)
                embed.set_thumbnail(url=member.avatar.url)
                embed.add_field(name=f"{user_emoji} Username", value=member.name, inline=True)
                embed.add_field(name="User ID", value=member.id, inline=True)
                embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
                embed.add_field(name="Joined Discord", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
                if member == member.guild.owner:
                    embed.add_field(name="Role", value="Server Owner", inline=True)
                elif member.guild_permissions.administrator:
                    embed.add_field(name="Role", value="Administrator", inline=True)
                elif member.guild_permissions.manage_messages:
                    embed.add_field(name="Role", value="Moderator", inline=True)
                else:
                    embed.add_field(name="Role", value="Member", inline=True)
                embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
                await ctx.send(embed=embed)
            else:
                await ctx.send("User not found.")
        except Exception as e:
            print(f"Error: {e}")
            await ctx.send("An error occurred while trying to fetch user information.")
        finally:
            mycursor.close()

async def setup(bot):
   await bot.add_cog(Whois(bot))