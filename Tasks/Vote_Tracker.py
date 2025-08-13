import datetime
from discord.ext import tasks
import discord

@tasks.loop(minutes=1, reconnect=True)
async def vote_track(bot):
    """
    Track votes for the bot and removes the vote role if the user has not voted in the last 12 hours.
    """
    try:
        guild_id = 1152949579407442050
        guild = bot.get_guild(guild_id)
        if guild is None:
            print(f"Guild with ID {guild_id} not found.")
            return
        votes = await bot.vote_tracker.find({})
        for vote in votes:
            user = discord.utils.get(guild.members, id=vote["user_id"])
            if user is None:
                print(f"User with ID {vote['user_id']} not found in guild {guild_id}.")
                continue

            if datetime.datetime.now() - vote["voted_at"] > datetime.timedelta(hours=12):
                guild = bot.get_guild(vote["guild_id"])
                if guild is None:
                    continue
                
                sett = await bot.settings.find_by_id(guild.id)
                if not sett:
                    sett = {}
                vote_role = guild.get_role(sett.get("vote_tracker", {}).get("vote_role", 0))

                if vote_role is None:
                    continue
                if vote_role not in user.roles:
                    continue
                await user.remove_roles(vote_role, reason="Vote expired")
                await bot.vote_tracker_document.delete_one({"_id": vote["_id"]})
    except Exception as e:
        print(f"Vote Tracker encountered an error: {e}")
