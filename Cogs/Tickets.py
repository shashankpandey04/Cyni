import discord
from cyni import is_staff
from discord.ext import commands
import datetime

# ticket_data = {
#     "_id": str(uuid.uuid4()),
#     "guild_id": guild.id,
#     "user_id": interaction.user.id,
#     "username": interaction.user.name,
#     "category_id": category_id,
#     "category_name": category.get("name"),
#     "channel_id": ticket_channel.id,
#     "status": "open",
#     "created_at": datetime.datetime.now().timestamp(),
#     "claimed_by": None,
#     "claimed_at": None,
#     "messages": [],
#     "transcript": None,
#     "participants": []
# }

# await db.tickets.insert_one(ticket_data)

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="ticket",
        description="Manage tickets",
    )
    async def ticket(self, ctx):
        """Base command for ticket management."""
        pass

    @ticket.command(
        name="claim",
        description="Claim a ticket",
    )
    @is_staff()
    @commands.guild_only()
    async def claim(self, ctx):
        """Claim a ticket."""

        ticket_data = await self.bot.db.tickets.find_one(
            {
                "guild_id": ctx.guild.id,
                "channel_id": ctx.channel.id,
                "status": "open"
            }
        )

        if not ticket_data:
            embed = discord.Embed(
                title="No Open Ticket",
                description="This channel does not have an open ticket.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
            

        await self.bot.db.tickets.update_one(
            {"_id": ticket_data["_id"]},
            {"$set": {"claimed_by": ctx.author.id, "claimed_at": datetime.datetime.now().timestamp()}}
        )

        embed = discord.Embed(
            title="Ticket Claimed",
            description=f"Your ticket has been claimed by {ctx.author.mention}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @ticket.command(
        name="leaderboard",
        description="View the ticket leaderboard",
    )
    @commands.guild_only()
    async def leaderboard(self, ctx):
        """View the ticket leaderboard."""
        leaderboard_data = await self.bot.db.tickets.aggregate([
            {"$match": {"guild_id": ctx.guild.id}},
            {"$group": {"_id": "$claimed_by", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]).to_list(length=None)

        if not leaderboard_data:
            embed = discord.Embed(
                title="Ticket Leaderboard",
                description="No tickets have been claimed yet.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title="Ticket Leaderboard",
            color=discord.Color.green()
        )

        for entry in leaderboard_data:
            user = self.bot.get_user(entry["_id"])
            embed.add_field(
                name=user.name if user else "Unknown User",
                value=f"Tickets Claimed: {entry['count']}",
                inline=False
            )

        await ctx.send(embed=embed)

    @ticket.command(
        name="add",
        description="Add a user to a ticket",
    )
    @is_staff()
    @commands.guild_only()
    async def add(self, ctx, user: discord.User):
        """Add a user to a ticket."""
        ticket_data = await self.bot.db.tickets.find_one(
            {
                "guild_id": ctx.guild.id,
                "channel_id": ctx.channel.id,
                "status": "open"
            }
        )

        if not ticket_data:
            embed = discord.Embed(
                title="No Open Ticket",
                description="This channel does not have an open ticket.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        await self.bot.db.tickets.update_one(
            {"_id": ticket_data["_id"]},
            {"$addToSet": {"participants": user.id}}
        )

        ticket_channel = ctx.channel
        await ticket_channel.set_permissions(
            user, read_messages=True,
            send_messages=True, attach_files=True,
            embed_links=True, read_message_history=True
            )

        embed = discord.Embed(
            title="User Added",
            description=f"{user.mention} has been added to the ticket.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @ticket.command(
        name="remove",
        description="Remove a user from a ticket",
    )
    @is_staff()
    @commands.guild_only()
    async def remove(self, ctx, user: discord.User):
        """Remove a user from a ticket."""
        ticket_data = await self.bot.db.tickets.find_one(
            {
                "guild_id": ctx.guild.id,
                "channel_id": ctx.channel.id,
                "status": "open"
            }
        )

        if not ticket_data:
            embed = discord.Embed(
                title="No Open Ticket",
                description="This channel does not have an open ticket.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        await self.bot.db.tickets.update_one(
            {"_id": ticket_data["_id"]},
            {"$pull": {"participants": user.id}}
        )

        ticket_channel = ctx.channel
        await ticket_channel.set_permissions(
            user, read_messages=False,
            send_messages=False, attach_files=False,
            embed_links=False, read_message_history=False
        )

        embed = discord.Embed(
            title="User Removed",
            description=f"{user.mention} has been removed from the ticket.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @ticket.command(
        name="close",
        description="Close a ticket",
    )
    @is_staff()
    @commands.guild_only()
    async def close(self, ctx):
        """Close a ticket."""
        ticket_data = await self.bot.db.tickets.find_one(
            {
                "guild_id": ctx.guild.id,
                "channel_id": ctx.channel.id,
                "status": "open"
            }
        )

        if not ticket_data:
            embed = discord.Embed(
                title="No Open Ticket",
                description="This channel does not have an open ticket.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        await self.bot.db.tickets.update_one(
            {"_id": ticket_data["_id"]},
            {"$set": {"status": "closed"}}
        )

        embed = discord.Embed(
            title="Ticket Closed",
            description="The ticket has been closed.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ticket(bot))