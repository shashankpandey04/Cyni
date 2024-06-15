import discord
from discord.ext import commands

from db import mycon
from utils import get_staff_or_management_roles

from cyni import dev, racial_slurs

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        await self.bot.process_commands(message)
        if message.author.bot:
            return
        if message.content.startswith("jsk shutdown"):
            if message.author.id in dev:
                await message.channel.send("<@800203880515633163> Get to work!")
                return
        if any(slur in message.content.lower() for slur in racial_slurs):
            if message.author.guild_permissions.administrator:
                #print("Admin Bypass")
                return
            await message.delete()
            await message.channel.send(f"{message.author.mention}, your message contained inappropriate content and was removed.")
            #print(f"{message} removed")
            return
        try:
            guild_id = message.guild.id
            user_id = message.author.id
            cursor = mycon.cursor()
            cursor.execute("SELECT * FROM server_config WHERE guild_id = %s", (guild_id,))
            server_config = cursor.fetchone()
            cursor.close()
            if server_config:
                guild_id, staff_roles, management_roles, mod_log_channel, premium, report_channel, blocked_search, anti_ping, anti_ping_roles, bypass_anti_ping_roles, loa_role, staff_management_channel,infraction_channel,promotion_channel,prefix,application_channel,message_quota = server_config
                if anti_ping == 1:
                    anti_ping_roles = anti_ping_roles or [] 
                    bypass_anti_ping_roles = bypass_anti_ping_roles or [] 
                    if message.mentions:
                        mentioned_user = message.mentions[0]
                        author_has_bypass_role = any(str(role.id) in bypass_anti_ping_roles for role in message.author.roles)
                        has_management_role = any(str(role.id) in anti_ping_roles for role in mentioned_user.roles)
                        if not author_has_bypass_role:
                            if has_management_role:
                                author_can_warn = any(str(role.id) in anti_ping_roles for role in message.author.roles)
                                if not author_can_warn:
                                    embed = discord.Embed(title="Anti-Ping Warning", description=f"{message.author.mention} attempted to ping {mentioned_user.mention} in {message.channel.mention}.", color=0xFF0000)
                                    embed.set_image(url="https://media.tenor.com/aslruXgPKHEAAAAM/discord-ping.gif")
                                    await message.channel.send(embed=embed)
            staff_or_management_roles = get_staff_or_management_roles(guild_id)
            user_roles = [role.id for role in message.author.roles]
            if any(role_id in user_roles for role_id in staff_or_management_roles):
                cursor = mycon.cursor()
                cursor.execute("INSERT INTO activity_logs (user_id, guild_id, messages_sent) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE messages_sent = messages_sent + 1",(user_id, guild_id))
                mycon.commit()
                cursor.close()
        except Exception as e:
            print(f"An error occurred while processing message: {e}")
            return
        
async def setup(bot):
    await bot.add_cog(OnMessage(bot))