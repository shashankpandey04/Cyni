import discord
from discord.ext import commands
import logging
from cyni import afk_users
import re
from datetime import timedelta

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

        n_word = re.compile(r'n[i1]gg[aeiou]r?', re.IGNORECASE)
        if n_word.search(message.content):
            await message.delete()
            await message.channel.send(f"{message.author.mention}, you can't say that word here!", delete_after=5)
            time = discord.utils.utcnow() + timedelta(seconds=5)
            try:
                await message.author.edit(timed_out_until=time,reason="N-word usage")
            except Exception:
                pass
            return

        if message.author.id in afk_users:
            del afk_users[message.author.id]
            await message.channel.send(
                f"Welcome back {message.author.mention}! I removed your AFK status.",
                delete_after=2
                )
            doc = {
                "_id" : message.author.id
            }
            await self.bot.afk.delete_by_id(doc)
            try:
                await message.author.edit(nick=message.author.display_name.replace("[AFK]",""))
            except Exception:
                pass

        for mentions in message.mentions:
            if mentions.id in afk_users:
                await message.channel.send(
                    f"`{mentions} `is currently AFK mode. Reason: {afk_users[mentions.id]}",
                    delete_after=15
                    )

        settings = await self.bot.settings.get(message.guild.id)
        if not settings:
            return
        anti_ping_module = settings.get("anti_ping_module", {})

        try:
            if anti_ping_module and anti_ping_module.get("enabled", False):
                if message.mentions:
                    for role in message.mentions[0].roles:
                        if role.id in anti_ping_module.get("affected_roles", []):
                            if any(role.id in anti_ping_module.get("exempt_roles", []) for role in message.author.roles):
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
        except KeyError:
            pass
        if not settings.get('basic_settings', {}).get('staff_roles') or not settings.get('basic_settings', {}).get('management_roles'):
            return
        staff_roles = settings.get("basic_settings", {}).get("staff_roles", [])

        if any(role.id in staff_roles for role in message.author.roles):
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
