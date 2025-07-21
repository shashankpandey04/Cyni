import discord
from discord.ext import tasks
import time
import asyncio

@tasks.loop(minutes=1, reconnect=True)
async def loa_check(bot):
    """
    Check for expired LOAs every minute.
    """
    start_time = time.time()

    try:
        # Fetch LOAs as a list to properly await the query
        loas = [loa async for loa in bot.loa.db.find({
            "accepted": True,
            "expired": False,
            "expiry": {"$lte": start_time},
            "dm_sent": False
        })]

        for loa in loas:
            try:
                guild = bot.get_guild(loa["guild_id"])
                if guild is None:
                    continue

                sett = await bot.settings.find_by_id(guild.id) or {}
                user = await guild.fetch_member(loa["user_id"])
                loa_role = guild.get_role(sett.get("leave_of_absence", {}).get("loa_role", 0))

                if user is None or loa_role is None:
                    continue

                # Remove role and update database
                await user.remove_roles(loa_role, reason="LOA Expired")
                await bot.loa.db.update_one(
                    {"_id": loa["_id"]},
                    {"$set": {"expired": True, "dm_sent": True}}
                )

                # Send DM to the user
                embed = discord.Embed(
                    title=f"Activity Notice Expired | {guild.name}",
                    description=f"Your {loa['type']} request in **{guild.name}** has expired.",
                    color=discord.Color.red()
                )
                try:
                    await user.send(embed=embed)
                except discord.Forbidden:
                    print(f"Could not DM {user} about expired LOA in {guild.name}")

            except Exception as e:
                print(f"Error processing LOA for guild {loa.get('guild_id')}: {e}")

    except Exception as e:
        print(f"Error fetching LOAs: {e}")