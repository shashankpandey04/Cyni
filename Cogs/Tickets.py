import discord
from cyni import is_staff
from discord.ext import commands
import datetime
import uuid
from dotenv import load_dotenv
import os
from Views.Tickets import TicketCloseView

load_dotenv()

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


    async def _collect_messages(self, channel: discord.TextChannel) -> list:
        """Collect all messages from the ticket channel."""
        messages = []
        async for message in channel.history(limit=None, oldest_first=True):
            if message.content or message.embeds:
                messages.append({
                    "author_id": message.author.id,
                    "author_name": message.author.name,
                    "content": message.content,
                    "created_at": message.created_at.timestamp(),
                    "attachments": [
                        {"url": attachment.url, "filename": attachment.filename} 
                        for attachment in message.attachments
                    ]
                })
        return messages

    async def _create_transcript(self, messages: list, closed_by: discord.Member, ticket_data: dict, reason: str) -> str:
        """Create and save transcript to database."""
        transcript_id = str(uuid.uuid4())
        transcript_data = {
            "_id": transcript_id,
            "ticket_id": ticket_data["_id"],
            "guild_id": ticket_data["guild_id"],
            "user_id": ticket_data["user_id"],
            "username": ticket_data["username"],
            "category_name": ticket_data["category_name"],
            "messages": messages,
            "closed_by": closed_by.id,
            "closed_by_name": closed_by.name,
            "created_at": datetime.datetime.now().timestamp(),
            "reason": reason
        }
        
        await self.bot.ticket_transcripts.insert_one(transcript_data)
        return transcript_id

    async def _send_transcript_notification(self, ticket_id: str, closed_by: discord.Member, ticket_category: dict, guild: discord.Guild, reason: str, ticket_data: dict):
        """Send transcript notification to designated channel."""
        transcript_channel_id = ticket_category.get("transcript_channel")
        if not transcript_channel_id:
            return

        transcript_channel = guild.get_channel(int(transcript_channel_id))
        if not transcript_channel:
            return
        
        ticked_doc = await self.bot.tickets.find_one({"_id": ticket_id})
        if not ticked_doc:
            return
        user = self.bot.get_user(ticked_doc["user_id"])
        
        base_url = os.getenv("BASE_URL", "https://cyni.quprdigital.tk")
        transcript_url = f"{base_url}/transcripts/{ticket_id}"
        
        transcript_embed = discord.Embed(
            title=f"Ticket Transcript: {ticket_category.get('name')}",
            description=f"Ticket from `{ticket_data['username']}` has been closed and archived.",
            color=0x5865F2,
            timestamp=datetime.datetime.now()
        )
        transcript_embed.add_field(name="Ticket ID", value=ticket_data["_id"], inline=True)
        transcript_embed.add_field(name="Closed By", value=closed_by.name, inline=True)
        transcript_embed.add_field(name="View Transcript", value=f"[Click Here]({transcript_url})", inline=False)
        transcript_embed.add_field(name="Reason", value=reason, inline=False)
        await transcript_channel.send(embed=transcript_embed)

        user_embed = discord.Embed(
            title=f"Ticket Closed in {guild.name}",
            description=(
                f"Thanks for reaching out to us, {user.mention}!\n\n"
                f"Your ticket has been closed. If you have any further questions, feel free to open a new ticket.\n\n"
                f"**Moderator Note:** ```{reason}```"
            ),
            color=0x5865F2,
            timestamp=datetime.datetime.now()
        )
        return await user.send(embed=user_embed)

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
    async def close(self, ctx, reason: str):
        """Close a ticket."""

        try:
            ticket_channel = ctx.channel
            ticket_category_id = ticket_channel.category.id
            existing_ticket_category = await self.bot.ticket_categories.find_one({"discord_category": ticket_category_id})
            if not existing_ticket_category:
                embed = discord.Embed(
                    title="Invalid Category",
                    description="This ticket is not in a valid ticket category.",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)
            
            if any(role.id in existing_ticket_category.get("support_roles", []) for role in ctx.author.roles) is False:
                embed = discord.Embed(
                    title="Insufficient Permissions",
                    description="You do not have permission to close this ticket.",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)
            guild = ctx.guild

            ticket_doc = await self.bot.tickets.find_one(
                {
                    "guild_id": ctx.guild.id,
                    "channel_id": ctx.channel.id,
                    "status": "open"
                }
            )
            ticket_channel = guild.get_channel(ticket_doc["channel_id"])
            if not ticket_channel:
                embed = discord.Embed(
                    title="Ticket Not Found",
                    description="The ticket channel could not be found.",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)
            
            try:
                messages = await self._collect_messages(ticket_channel)

                transcript_id = await self._create_transcript(messages, ctx.author, ticket_doc, reason)

                await self._send_transcript_notification(ticket_doc["_id"], ctx.author, existing_ticket_category, guild, reason, ticket_doc)

                base_url = os.getenv("BASE_URL", "https://cyni.quprdigital.tk")
                transcript_url = f"{base_url}/transcripts/{ticket_doc['_id']}"
                
                final_embed = discord.Embed(
                    title="Ticket Closed",
                    description=f"This ticket has been closed by {ctx.author.mention}.",
                    color=0xED4245,
                    timestamp=datetime.datetime.now()
                )
                final_embed.add_field(
                    name="Transcript", 
                    value=f"[Click here to view the ticket transcript]({transcript_url})",
                    inline=False
                )

                await ctx.send(embed=final_embed)

                return await ticket_channel.delete(reason=f"Ticket deleted by {ctx.author.name}")

            except Exception as e:
                self.bot.logger.error(f"Failed to delete ticket channel: {e}")
                await ctx.send(
                    embed=discord.Embed(
                        title="Error",
                        description=f"Failed to delete ticket. Please contact an administrator. ```{e}```",
                        color=discord.Color.red()
                    )
                )
        except Exception as e:
            self.bot.logger.error(f"Failed to close ticket: {e}")
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"Failed to close ticket. Please contact an administrator. ```{e}```",
                    color=discord.Color.red()
                )
            )

    # @ticket.command(
    #     name="closerequest",
    #     description="Request to close a ticket",
    # )
    # async def close_request(self, ctx, reason: str):
    #     """Request to close a ticket."""
    #     try:
    #         ticket_data = await self.bot.db.tickets.find_one(
    #             {
    #                 "guild_id": ctx.guild.id,
    #                 "channel_id": ctx.channel.id,
    #                 "status": "open"
    #             }
    #         )

    #         if not ticket_data:
    #             embed = discord.Embed(
    #                 title="No Open Ticket",
    #                 description="This channel does not have an open ticket.",
    #                 color=discord.Color.red()
    #             )
    #             return await ctx.send(embed=embed)

    #         category_doc = await self.bot.ticket_categories.find_one(
    #             {
    #                 "discord_category": ctx.channel.category.id,
    #                 "guild_id": ctx.guild.id
    #             }
    #         )
    #         support_roles = category_doc.get("support_roles", [])
    #         if not support_roles:
    #             embed = discord.Embed(
    #                 title="No Support Roles",
    #                 description="This ticket does not have any support roles configured. Please contact an administrator.",
    #                 color=discord.Color.red()
    #             )
    #             return await ctx.send(embed=embed)
        
    #         if not any(role.id in support_roles for role in ctx.author.roles):
    #             embed = discord.Embed(
    #                 title="Insufficient Permissions",
    #                 description="You do not have permission to request to close this ticket.",
    #                 color=discord.Color.red()
    #             )
    #             return await ctx.send(embed=embed)
            
    #         embed = discord.Embed(
    #             title="Close Request",
    #             description=f"{ctx.author.mention} has requested to close this ticket.\n\n**Reason:** ```{reason}```",
    #             color=discord.Color.orange(),
    #             timestamp=datetime.datetime.now()
    #         )
    #         channel_category = ctx.channel.category
    #         category = self.bot.ticket_categories.find_one({"discord_category": channel_category.id})
    #         user = self.bot.get_user(ticket_data["user_id"])
    #         view = TicketCloseView(user, ticket_data, ctx.guild, category, reason)
    #         await ctx.send(embed=embed, view=view)
    #     except Exception as e:
    #         self.bot.logger.error(f"Failed to request ticket close: {e}")
    #         await ctx.send(
    #             embed=discord.Embed(
    #                 title="Error",
    #                 description=f"Failed to request ticket close. Please contact an administrator. ```{e}```",
    #                 color=discord.Color.red()
    #             )
    #         )

async def setup(bot):
    await bot.add_cog(Ticket(bot))