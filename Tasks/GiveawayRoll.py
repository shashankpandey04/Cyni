import discord
from discord.ext import tasks
import time
import random
from datetime import datetime

@tasks.loop(minutes=1, reconnect=True)
async def giveaway_roll(bot):
    """
    Check for expired giveaways every minute.
    Edit the giveaway message in the channel to indicate that the giveaway has ended.
    Announce the winner in the channel.
    """
    current_time = datetime.now().timestamp()
    
    # Find expired giveaways that haven't been rolled yet
    expired_giveaways = await bot.giveaways.find({
        "duration_epoch": {"$lte": current_time},
        "completed": {"$exists": False}
    })
    
    for giveaway in expired_giveaways:
        try:
            guild_id = giveaway.get("guild_id")
            guild = bot.get_guild(guild_id)
            
            if not guild:
                continue
                
            message_id = giveaway.get("message_id")
            channel_id = int(giveaway.get("channel_id", 0))
            
            # If channel_id isn't in giveaway data, try to find the message in all channels
            if channel_id == 0:
                message = None
                for channel in guild.text_channels:
                    try:
                        message = await channel.fetch_message(message_id)
                        if message:
                            channel_id = channel.id
                            break
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                        continue
            else:
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue
                    
                try:
                    message = await channel.fetch_message(message_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    continue
            
            if not message:
                # Mark as completed even if message wasn't found to avoid continuous processing
                await bot.giveaways.update_one(
                    {"message_id": message_id},
                    {"completed": True, "error": "Message not found"}
                )
                continue
            
            # Get participants and determine winners
            participants = giveaway.get("participants", [])
            total_winners = min(giveaway.get("total_winner", 1), len(participants))
            
            if participants and total_winners > 0:
                winners = random.sample(participants, total_winners)
                winners_mentions = [f"<@{winner}>" for winner in winners]
                
                # Update the giveaway embed to show it has ended
                embed = message.embeds[0] if message.embeds else None
                if embed:
                    embed_dict = embed.to_dict()
                    description = embed_dict.get("description", "")
                    
                    # Add winners to description if they're not already there
                    if not any(f"Winner(s):" in line for line in description.split("\n")):
                        description += f"\n\nWinner(s): {', '.join(winners_mentions)}"
                        embed_dict["description"] = description
                        
                        # Create new embed with updated description
                        new_embed = discord.Embed.from_dict(embed_dict)
                        try:
                            await message.edit(embed=new_embed)
                        except discord.HTTPException:
                            pass
                
                # Send announcement in the channel
                host_id = giveaway.get("host")
                title = giveaway.get("title", "Giveaway")
                
                announcement = (
                    f"<:giveaway:1268849874233725000> Congratulations to {', '.join(winners_mentions)} "
                    f"for winning the **{title}** giveaway!\n"
                    f"Hosted by <@{host_id}>"
                )
                await channel.send(announcement)
            else:
                # No participants or winners
                await channel.send(f"<:declined:1268849944455024671> No one participated in the **{giveaway.get('title', 'Giveaway')}** giveaway or not enough participants.")
            
            # Mark giveaway as completed in database
            await bot.giveaways.update_one(
                {"message_id": message_id},
                {
                    "completed": True,
                    "winners": winners if participants and total_winners > 0 else [],
                    "end_time": current_time
                }
            )
            
        except Exception as e:
            print(f"Error processing giveaway {giveaway.get('message_id')}: {e}")
            # Mark as errored to prevent endless retries
            await bot.giveaways.update_one(
                {"message_id": giveaway.get("message_id")},
                {"completed": True, "error": str(e)}
            )
