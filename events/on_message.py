import discord
from discord.ext import commands
import logging
from cyni import afk_users

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        if message.author.bot:
            return
        
        if message.content == "ping":
            await message.channel.send("🟢 Pong!")

        if message.author.id in afk_users:
            del afk_users[message.author.id]
            await message.channel.send(
                f"Welcome back {message.author.mention}! I removed your AFK status.",
                delete_after=15
                )

        for mentions in message.mentions:
            if mentions.id in afk_users:
                pressence = mentions.status.value
                await message.channel.send(
                    f"{mentions.mention} is currently AFK and {pressence}. Reason: {afk_users[mentions.id]}",
                    delete_after=15
                    )

        settings = await self.bot.settings.get(message.guild.id)
        if not settings:
            return

        try:
            anti_ping_module = settings["anti_ping_module"]
        except KeyError:
            anti_ping_module = None
        
        if anti_ping_module and anti_ping_module["enabled"]:
            if message.mentions:
                for role in message.mentions[0].roles:
                    if role.id in anti_ping_module["affected_roles"]:
                        for role in message.author.roles:
                            if role.id in anti_ping_module["exempt_roles"]:
                                return
                        await message.channel.send(
                            embed=discord.Embed(
                                title="Anti-Ping Warning",
                                description=f"{message.author.mention} please do not ping users with the role {role.mention}.",
                                color=discord.Color.red()
                            ).set_image(
                                url="https://media.tenor.com/aslruXgPKHEAAAAM/discord-ping.gif"
                            ),
                            delete_after=15
                        )
        
        if not settings["basic_settings"]["staff_roles"] or not settings["basic_settings"]["management_roles"]:
            return
        
        staff_roles = settings["basic_settings"]["staff_roles"]

        for role in message.author.roles:
            if role.id in staff_roles:
                staff = await self.bot.staff_activity.find_by_id(message.guild.id)
                if not staff:
                    await self.bot.staff_activity.insert(
                        {
                            "_id": message.guild.id,
                            "staff": [
                                {
                                    "_id": message.author.id,
                                    "messages": 1
                                }
                            ]
                        }
                    )
                else:
                    for member in staff["staff"]:
                        if member["_id"] == message.author.id:
                            await self.bot.staff_activity.upsert(
                                {
                                    "_id": message.guild.id,
                                    "staff": [
                                        {
                                            "_id": message.author.id,
                                            "messages": member["messages"] + 1
                                        }
                                    ]
                                }
                            )
                return

async def setup(bot):
    await bot.add_cog(OnMessage(bot))
