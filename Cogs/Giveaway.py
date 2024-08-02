import discord
from discord.ext import commands
from cyni import is_management
from utils.constants import BLANK_COLOR
from datetime import datetime, timedelta
import random
from utils.utils import log_command_usage
import collections.abc
import re

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_duration(self, duration):
        """
        Parse a duration string and return the total duration in seconds.
        Supports days (d), weeks (w), hours (h), minutes (m), and seconds (s).
        """
        regex = r"(?:(\d+)\s*d(?:ays?)?)?\s*(?:(\d+)\s*w(?:eeks?)?)?\s*(?:(\d+)\s*h(?:ours?)?)?\s*(?:(\d+)\s*m(?:inutes?)?)?\s*(?:(\d+)\s*s(?:econds?)?)?"
        matches = re.match(regex, duration)
        if not matches:
            return None

        days = int(matches.group(1)) if matches.group(1) else 0
        weeks = int(matches.group(2)) if matches.group(2) else 0
        hours = int(matches.group(3)) if matches.group(3) else 0
        minutes = int(matches.group(4)) if matches.group(4) else 0
        seconds = int(matches.group(5)) if matches.group(5) else 0

        total_seconds = timedelta(days=days, weeks=weeks, hours=hours, minutes=minutes, seconds=seconds).total_seconds()
        return int(total_seconds)

    @commands.hybrid_group(
        name="giveaway",
        extras={
            "category": "Giveaway"
        }
    )
    async def giveaway(self, ctx):
        pass

    @giveaway.command(
        name="create",
        extras={
            "category": "Giveaway"
        }
    )
    @is_management()
    async def create(self, ctx, title: str, *, description: str, duration: str, total_winner: int, host: discord.Member):
        """
        Create a giveaway.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Giveaway Create for {title}")
        duration_seconds = self.parse_duration(duration)
        if duration_seconds is None:
            await ctx.send("Invalid duration format. Please use formats like '2d', '1w', '3h', '45m', '30s'.")
            return
        
        end_time = datetime.now() + timedelta(seconds=duration_seconds)
        end_time_epoch = int(end_time.timestamp())

        embed = discord.Embed(
            title=f"<:giveaway:1268849874233725000> {title}",
            description=f"""
            {description}\n\nEnds At: <t:{end_time_epoch}:F>\nTotal Winner: {total_winner}\nHost: {host.mention}""",
            color=BLANK_COLOR
        )
        msg = await ctx.send(embed=embed)
        message_id = msg.id
        embed.set_footer(text=f"Giveaway ID: {message_id}")
        await msg.edit(embed=embed)
        await msg.add_reaction("🎉")
        await self.bot.giveaways.insert_one({
            "message_id": message_id,
            "guild_id": ctx.guild.id,
            "title": title,
            "description": description,
            "duration_epoch": end_time_epoch,
            "total_winner": total_winner,
            "host": host.id,
            "participants": []
        })

    @giveaway.command(
        name="roll",
        extras={
            "category": "Giveaway"
        }
    )
    @is_management()
    async def roll(self, ctx, message_id: str):
        """
        Roll a giveaway.
        """
        message_id = int(message_id)
        giveaway = await self.bot.giveaways.find_one({"message_id": message_id})
        if giveaway is None:
            await ctx.send("<:declined:1268849944455024671> Giveaway not found.")
            return
        if datetime.now().timestamp() < giveaway["duration_epoch"]:
            await ctx.send("<:giveaway:1268849874233725000> Giveaway is still active.")
            return
        participants = giveaway["participants"]
        if len(participants) < giveaway["total_winner"]:
            await ctx.send("<:declined:1268849944455024671>  Not enough participants.")
            return
        winners = random.sample(participants, giveaway["total_winner"])
        await ctx.send(f"<:giveaway:1268849874233725000> Congratulations to {', '.join([f'<@{winner}>' for winner in winners])} for winning the {giveaway['title']} giveaway!\nHosted by <@{giveaway['host']}>")
        msg = await ctx.fetch_message(message_id)
        embed = msg.embeds[0]
        embed.description += f"\n\nWinner(s): {', '.join([f'<@{winner}>' for winner in winners])}"
        await msg.edit(embed=embed)

    @giveaway.command(
        name="list",
        extras={
            "category": "Giveaway"
        }
    )
    @is_management()
    async def list(self, ctx):
        """
        List all active giveaways.
        """
        giveaways = await self.bot.giveaways.find({"guild_id": ctx.guild.id})
        
        if not giveaways:
            await ctx.send("No active giveaways.")
            return
        active_giveaways = [giveaway for giveaway in giveaways if datetime.now().timestamp() < giveaway["duration_epoch"]]

        if not active_giveaways:
            await ctx.send("No active giveaways.")
            return
        embed = discord.Embed(
            title="Active Giveaways",
            color=BLANK_COLOR
        )
        for giveaway in active_giveaways:
            embed.add_field(
                name=f"{giveaway['title']} - {giveaway['message_id']}",
                value=f"Hosted by <@{giveaway['host']}>\nEnds at <t:{giveaway['duration_epoch']}:F>",
                inline=False
            )
        await ctx.send(embed=embed)
        
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """
        Adds a user to the participants list when they react with 🎉.
        """
        if user.bot:
            return
        
        if str(reaction.emoji) != "🎉":
            return

        message_id = reaction.message.id
        giveaway = await self.bot.giveaways.find_one({"message_id": message_id})
        if giveaway is None:
            return

        if user.id not in giveaway["participants"]:
            giveaway["participants"].append(user.id)
            await self.bot.giveaways.update({"message_id": message_id}, {"participants": giveaway["participants"]})
            await reaction.message.channel.send(f"{user.mention} has entered the giveaway!", delete_after=2)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """
        Removes a user from the participants list when they remove their reaction.
        """
        if user.bot:
            return
        
        if str(reaction.emoji) != "🎉":
            return

        message_id = reaction.message.id
        giveaway = await self.bot.giveaways.find_one({"message_id": message_id})
        if giveaway is None:
            return

        if user.id in giveaway["participants"]:
            giveaway["participants"].remove(user.id)
            await self.bot.giveaways.update({"message_id": message_id}, {"participants": giveaway["participants"]})
            await reaction.message.channel.send(f"{user.mention} has left the giveaway!", delete_after=2)

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
