import datetime
from discord.ext import tasks
import time

@tasks.loop(minutes=1, reconnect=True)
async def vote_track(bot):
    """
    Track votes for the bot and removes the vote role if the user has not voted in the last 12 hours.
    """
    start_time = time.time()
    try:
        cursor = await bot.vote_tracker_document.find({})
        async for vote in cursor:
            user = bot.get_user(vote["user_id"])
            if user is None:
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
        print("Vote Tracker completed successfully.")
    except Exception as e:
        print(f"Vote Tracker encountered an error: {e}")
                
    print(f"Vote Tracker took {time.time() - start_time} seconds.")

    