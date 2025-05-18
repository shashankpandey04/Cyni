from fastapi import FastAPI, APIRouter, Header, HTTPException, Request
from discord.ext import commands
from pydantic import BaseModel
import discord
import uvicorn
import asyncio
import logging
from typing import Annotated
import os
from dotenv import load_dotenv
import datetime
import pymongo
import motor.motor_asyncio
import threading
from cyni import cad_access_check, cad_administrator_check, cad_operator_check
import uuid

# Load the environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Define the FastAPI app
api = FastAPI()

bot_token = os.getenv("PRODUCTION_TOKEN") if os.getenv("PRODUCTION_TOKEN") else os.getenv("DEV_TOKEN")

mongo = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGO_URI'))
db = mongo["cyni"] if os.getenv("PRODUCTION_TOKEN") else mongo["dev"]

import logging

logging.basicConfig(level=logging.INFO)

# Data Model for Application Status
class ApplicationStatus(BaseModel):
    guild_id: int
    user_id: int
    application_name: str
    new_status: str
    pass_role: int
    fail_role: int
    result_channel: int
    note: str | None = "Not provided."

class CAD_Team(BaseModel):
    guild_id: int
    team: str
    owner_id: int
    co_owners: list[int] = []
    members: list[int]
    pending_members: list[int]
    blacklist: list[int]
    icon_url: str | None = None
    created_at: int

class CAD_Log(BaseModel):
    guild_id: int
    created_by: int
    team: str
    punishment: str
    reason: str | None = None
    created_at: int

class TicketEmbedRequest(BaseModel):
    guild_id: int
    category_id: str


# Authorization validation function
async def validate_authorization(bot, token: str):
    """Validate the authorization token."""
    static_token = bot_token
    if token == static_token:
        return True
    return False


# API Routes
class APIRoutes:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.router = APIRouter()
        for attr in dir(self):
            if attr.startswith(("GET_", "POST_", "PATCH_", "DELETE_")) and not attr.startswith("_"):
                method = attr.split("_")[0]
                route = attr[len(method) + 1:]
                self.router.add_api_route(
                    f"/{route}",
                    getattr(self, attr),
                    methods=[method.upper()],
                )

    def GET_status(self):
        """API status check."""
        return {"guilds": len(self.bot.guilds), "ping": round(self.bot.latency * 1000)}

    async def GET_guilds(self, authorization: Annotated[str | None, Header()]):
        """Get a list of guilds the bot is in."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Invalid authorization")
        if not await validate_authorization(self.bot, authorization):
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")
        guilds = [{"id": guild.id, "name": guild.name} for guild in self.bot.guilds]
        return guilds
    
    async def POST_mutual_guilds(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Get mutual guilds between the bot and a user."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Invalid authorization")
        if not await validate_authorization(self.bot, authorization):
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")
        json_data = await request.json()
        user_id = json_data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not provided")
        user = self.bot.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        mutual_guilds = [
            [
                guild for guild in self.bot.guilds if guild.get_member(user_id)] for user_id in user.mutual_guilds
            ]
        return mutual_guilds

    async def POST_guild_roles(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Get a list of roles in a guild."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Invalid authorization")
        if not await validate_authorization(self.bot, authorization):
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")
        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        if not guild_id:
            raise HTTPException(status_code=400, detail="Guild ID not provided")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        roles = [{"id": role.id, "name": role.name} for role in guild.roles]
        return roles
    
    async def POST_guild_channels(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Get a list of channels in a guild."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Invalid authorization")
        if not await validate_authorization(self.bot, authorization):
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")
        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        if not guild_id:
            raise HTTPException(status_code=400, detail="Guild ID not provided")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        channels = [{"id": channel.id, "name": channel.name} for channel in guild.channels]
        return channels, 200

    async def POST_guild_members(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Get a list of members in a guild."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Invalid authorization")
        if not await validate_authorization(self.bot, authorization):
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")
        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        if not guild_id:
            raise HTTPException(status_code=400, detail="Guild ID not provided")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        members = [{"id": member.id, "name": member.name} for member in guild.members]
        return members, 200
    
    async def POST_change_config(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Change the bot configuration."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Invalid authorization")
        if not await validate_authorization(self.bot, authorization):
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")
        json_data = await request.json()
        doc = await db.settings.find_one({"_id": json_data["_id"]})
        if not doc:
            raise HTTPException(status_code=404, detail="Settings not found")
        await db.settings.update_one({"_id": json_data["_id"]}, {"$set": json_data})
        return {"message": "Configuration updated successfully."}, 200

    async def POST_notify_user(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Notify a user about their application status."""
        logger.debug("Received POST request to notify user about application status.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        status = ApplicationStatus(**json_data)

        guild = self.bot.get_guild(status.guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {status.guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        member = guild.get_member(status.user_id)
        if not member:
            logger.error(f"User  not found for ID: {status.user_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="User  not found")

        pass_role = guild.get_role(status.pass_role)
        fail_role = guild.get_role(status.fail_role)

        try:
            if status.new_status == "accepted" and pass_role:
                logger.info(f"Notifying user {member.name} about application acceptance.")
                embed = discord.Embed(
                    title="✅ Application Accepted",
                    description=f"Congratulations! Your application has been accepted in **{guild.name}**.",
                    color=discord.Color.green(),
                )

                embed.add_field(name="Application Name", value=status.application_name, inline=False)
                embed.add_field(name="Note", value=status.note, inline=False)
                embed.set_footer(text="Thank you for your application!", icon_url=guild.icon.url if guild.icon else "")

                await member.send(embed=embed)
                logger.debug(f"Sent acceptance message to {member.name}.")

                result_channel = guild.get_channel(status.result_channel)
                if result_channel:
                    await result_channel.send(f"{member.mention}", embed=embed)
                    logger.debug(f"Sent acceptance notification to result channel: {result_channel.name}.")
                else:
                    logger.warning(f"Result channel not found for ID: {status.result_channel}")

            elif status.new_status == "rejected" and fail_role:
                logger.info(f"Notifying user {member.name} about application rejection.")
                embed = discord.Embed(
                    title="❌ Application Rejected",
                    description=f"Your application has been rejected in **{guild.name}**.",
                    color=discord.Color.red(),
                )

                embed.add_field(name="Application Name", value=status.application_name, inline=False)
                embed.add_field(name="Note", value=status.note, inline=False)
                embed.set_footer(text="Thank you for your application!", icon_url=guild.icon.url if guild.icon else "")
                await member.send(embed=embed)
                logger.debug(f"Sent rejection message to {member.name}.")

                result_channel = guild.get_channel(status.result_channel)
                if result_channel:
                    await result_channel.send(f"{member.mention}", embed=embed)
                    logger.debug(f"Sent rejection notification to result channel: {result_channel.name}.")
                else:
                    logger.warning(f"Result channel not found for ID: {status.result_channel}")

            else:
                logger.error("Invalid application status received.")
                raise HTTPException(status_code=400, detail="Invalid application status")

        except Exception as e:
            logger.error(f"Failed to notify user: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to process notification")
        
        
        notification_data = {
            "user_id": status.user_id,
            "title" : "Application Status Update",
            "message": f"Your application for {status.application_name} has been {status.new_status} in {guild.name}.",
            "created_at": str(datetime.datetime.now()),
            "from": f"{guild.name}",
        }
        await db.notifications.insert_one(notification_data)
        return {"message": "Notification sent successfully"}
    
    async def POST_notify_ban_appeal(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Notify a user about their application status."""
        logger.debug("Received POST request to notify user about ban appeal status.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        user_id = json_data.get("user_id")
        guild_id = json_data.get("guild_id")
        appeal_id = json_data.get("appeal_id")
        user_name = json_data.get("user_name")

        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        member = self.bot.get_user(user_id)

        sett = await db.settings.find_one({"_id": guild_id})
        if not sett:
            logger.error(f"Settings not found for guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Settings not found")
        
        ban_appeal_channel_id = sett.get("moderation_module", {}).get("ban_appeal_channel", None)
        
        if not ban_appeal_channel_id:
            logger.error(f"Ban appeal channel not found in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Ban appeal channel not found")
        
        ban_appeal_channel = guild.get_channel(int(ban_appeal_channel_id))
        if not ban_appeal_channel:
            logger.error(f"Ban appeal channel not found in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Ban appeal channel not found")
        
        embed = discord.Embed(
            title="New Ban Appeal",
            description=f"**{user_name}** has submitted a ban appeal.\n**User ID:** {user_id}\n**Appeal ID:** {appeal_id}\n**Posted at:** <t:{int(datetime.datetime.now().timestamp())}:R>",
            color=0x2F3136
        )
        view = discord.ui.View()
        url_button = discord.ui.Button(
            label="View Ban Appeal", 
            url=f"https://cyni.quprdigital.tk/banappeal/logs/{guild_id}/{appeal_id}",
            style=discord.ButtonStyle.url
        )
        view.add_item(url_button)
        await ban_appeal_channel.send(embed=embed, view=view)
        return {"message": "Ban appeal notification sent successfully."}
    
    async def POST_notify_ban_appeal_status(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Notify a user about their ban appeal status."""
        logger.debug("Received POST request to notify user about ban appeal status.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        user_id = json_data.get("user_id")
        guild_id = json_data.get("guild_id")
        appeal_id = json_data.get("appeal_id")
        status = json_data.get("status")

        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        member = guild.get_member(int(user_id))
        if not member:
            logger.error(f"User  not found for ID: {user_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="User  not found")
        
        appeal_doc = await db.ban_appeals.find_one({"appeal_id": appeal_id})
        if not appeal_doc:
            logger.error(f"Ban appeal not found for ID: {appeal_id}")
            raise HTTPException(status_code=404, detail="Ban appeal not found")

        await db.ban_appeals.update_one({"_id": appeal_id}, {"$set": {"status": status}})
        guild_invite = await guild.text_channels[0].create_invite()
        if status == "accepted":
            try:
                await guild.unban(member)
            except Exception as e:
                raise HTTPException(status_code=500, detail="Failed to unban user.")
        view = discord.ui.View()
        url_button = discord.ui.Button(
            label="Join Server", 
            url=guild_invite.url,
            style=discord.ButtonStyle.url
        )
        view.add_item(url_button)
        if status == "accepted":
            embed = discord.Embed(
                title=f"Ban Appeal Status",
                description=f"Your ban appeal has been accepted by the moderation team in **{guild.name}**.",
                color=discord.Color.green()
            )
            await member.send(embed=embed, view=view)
        elif status == "denied":
            embed = discord.Embed(
                title=f"Ban Appeal Status",
                description=f"Your ban appeal has been rejected by the moderation team in **{guild.name}**.",
                color=discord.Color.red()
            )
            await member.send(embed=embed)

    async def POST_loa_update(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Update the status of a LOA request."""
        logger.debug("Received POST request to update LOA status.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        user_id = json_data.get("user_id")
        guild_id = json_data.get("guild_id")
        loa_id = json_data.get("loa_id")
        status = json_data.get("status")

        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        member = guild.get_member(user_id)
        if not member:
            logger.error(f"User  not found for ID: {user_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="User  not found")

        loa_doc = await db.loa.find_one({"_id": loa_id})
        if not loa_doc:
            logger.error(f"LOA request not found for user: {member.name}")
            raise HTTPException(status_code=404, detail="LOA request not found")
        if status == "accepted":
            await db.loa.update_one({"_id": loa_id}, {"$set": {"accepted": True}})
            embed = discord.Embed(
                title=f"LOA Approved in {guild.name}",
                description=f"Your leave of absence request has been approved.",
                color=discord.Color.green(),
            )
            await member.send(embed=embed)

        elif status == "denied":
            await db.loa.update_one({"_id": loa_id}, {"$set": {"denied": True}})
            embed = discord.Embed(
                title=f"LOA Rejected in {guild.name}",
                description=f"Your leave of absence request has been rejected.",
                color=discord.Color.red(),
            )
            await member.send(embed=embed)

        return {"message": "LOA status updated successfully"}

    async def POST_send_ticket_embed(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Send a ticket embed to a Discord channel."""
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        category_id = json_data.get("category_id")
        
        if not guild_id or not category_id:
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Get guild
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        
        # Get ticket category
        category = await db.ticket_categories.find_one({"_id": category_id, "guild_id": int(guild_id)})
        if not category:
            raise HTTPException(status_code=404, detail="Ticket category not found")
        
        # Get channel
        channel = guild.get_channel(int(category.get("ticket_channel")))
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # Create embed
        embed = discord.Embed(
            title=category.get("embed", {}).get("title", "Support Ticket"),
            description=category.get("embed", {}).get("description", "Click the button below to create a ticket"),
            color=category.get("embed", {}).get("color", 0x5865F2)
        )
        
        if guild.icon:
            embed.set_footer(text=f"{guild.name}", icon_url=guild.icon.url)
        else:
            embed.set_footer(text=f"{guild.name}")
        
        # Create button for ticket creation
        class TicketButton(discord.ui.Button):
            def __init__(self, emoji, label, custom_id, style):
                super().__init__(emoji=emoji, label=label, custom_id=custom_id, style=style)
                
            async def callback(self, interaction: discord.Interaction):
                # Create a ticket
                await interaction.response.defer(ephemeral=True)
                
                # Check if user already has an open ticket in this category
                existing_ticket = await db.tickets.find_one({
                    "guild_id": guild.id,
                    "user_id": interaction.user.id,
                    "category_id": category_id,
                    "status": "open"
                })
                
                if existing_ticket:
                    channel_id = existing_ticket.get("channel_id")
                    channel = guild.get_channel(channel_id)
                    if channel:
                        return await interaction.followup.send(
                            f"You already have an open ticket: {channel.mention}", 
                            ephemeral=True
                        )
                
                # Create ticket channel
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                
                # Add permissions for support roles
                for role_id in category.get("support_roles", []):
                    role = guild.get_role(role_id)
                    if role:
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                
                # Create the ticket channel
                ticket_id = str(await db.tickets.count_documents({"guild_id": guild.id})) + 1
                channel_name = f"ticket-{ticket_id}-{interaction.user.name}"
                
                try:
                    ticket_channel = await guild.create_text_channel(
                        name=channel_name[:100],  # Discord has a character limit for channel names
                        overwrites=overwrites,
                        reason=f"Ticket created by {interaction.user.name}"
                    )
                except Exception as e:
                    logger.error(f"Failed to create ticket channel: {e}")
                    return await interaction.followup.send(
                        "Failed to create ticket channel. Please contact an administrator.",
                        ephemeral=True
                    )
                
                # Create ticket record in database
                ticket_data = {
                    "_id": str(uuid.uuid4()),
                    "guild_id": guild.id,
                    "user_id": interaction.user.id,
                    "username": interaction.user.name,
                    "category_id": category_id,
                    "category_name": category.get("name"),
                    "channel_id": ticket_channel.id,
                    "status": "open",
                    "created_at": datetime.datetime.now().timestamp()
                }
                
                await db.tickets.insert_one(ticket_data)
                
                # Send welcome message in ticket channel
                welcome_embed = discord.Embed(
                    title=f"Ticket: {category.get('name')}",
                    description=f"Thank you for creating a ticket, {interaction.user.mention}!\n\nSupport will be with you shortly.",
                    color=0x5865F2,
                    timestamp=datetime.datetime.now()
                )
                
                # Create UI components for ticket management
                close_button = discord.ui.Button(
                    style=discord.ButtonStyle.danger, 
                    label="Close Ticket", 
                    custom_id=f"close_ticket:{ticket_data['_id']}"
                )
                
                class TicketActionView(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=None)
                        self.add_item(close_button)
                    
                    @discord.ui.button(style=discord.ButtonStyle.danger, label="Close Ticket", custom_id=f"close_ticket:{ticket_data['_id']}")
                    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
                        # Check if user is ticket creator or has support role
                        is_creator = interaction.user.id == ticket_data["user_id"]
                        has_support_role = False
                        
                        for role_id in category.get("support_roles", []):
                            role = guild.get_role(role_id)
                            if role and role in interaction.user.roles:
                                has_support_role = True
                                break
                                
                        if not (is_creator or has_support_role):
                            return await interaction.response.send_message(
                                "You don't have permission to close this ticket.",
                                ephemeral=True
                            )
                        
                        # Update ticket status
                        await db.tickets.update_one(
                            {"_id": ticket_data["_id"]},
                            {"$set": {"status": "closed"}}
                        )
                        
                        # Send closing message
                        closing_embed = discord.Embed(
                            title="Ticket Closed",
                            description=f"This ticket has been closed by {interaction.user.mention}.",
                            color=0xED4245,
                            timestamp=datetime.datetime.now()
                        )
                        
                        delete_button = discord.ui.Button(
                            style=discord.ButtonStyle.danger, 
                            label="Delete Ticket", 
                            custom_id=f"delete_ticket:{ticket_data['_id']}"
                        )
                        
                        class DeleteView(discord.ui.View):
                            def __init__(self):
                                super().__init__(timeout=None)
                                self.add_item(delete_button)
                            
                            @discord.ui.button(style=discord.ButtonStyle.danger, label="Delete Ticket", custom_id=f"delete_ticket:{ticket_data['_id']}")
                            async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
                                if not has_support_role:
                                    return await interaction.response.send_message(
                                        "Only staff can delete tickets.",
                                        ephemeral=True
                                    )
                                
                                await interaction.response.defer()
                                
                                # Archive ticket messages
                                messages = []
                                async for message in ticket_channel.history(limit=None, oldest_first=True):
                                    if message.content:
                                        messages.append({
                                            "author_id": message.author.id,
                                            "author_name": message.author.name,
                                            "content": message.content,
                                            "created_at": message.created_at.timestamp()
                                        })
                                
                                # Save messages to database
                                if messages:
                                    await db.ticket_messages.insert_many([
                                        {
                                            "ticket_id": ticket_data["_id"],
                                            "guild_id": guild.id,
                                            **msg
                                        } for msg in messages
                                    ])
                                
                                # Delete channel
                                try:
                                    await ticket_channel.delete(reason=f"Ticket deleted by {interaction.user.name}")
                                except Exception as e:
                                    logger.error(f"Failed to delete ticket channel: {e}")
                        
                        await interaction.response.send_message(embed=closing_embed, view=DeleteView())
                
                await ticket_channel.send(f"{interaction.user.mention} {' '.join([f'<@&{role_id}>' for role_id in category.get('support_roles', [])])}", embed=welcome_embed, view=TicketActionView())
                
                # Let the user know the ticket was created
                await interaction.followup.send(
                    f"Ticket created successfully! Please check {ticket_channel.mention}",
                    ephemeral=True
                )
        
        # Create the view with the button
        view = discord.ui.View(timeout=None)
        button = TicketButton(
            emoji=category.get("emoji", "🎫"),
            label=f"Create {category.get('name')} Ticket",
            custom_id=f"create_ticket:{category_id}",
            style=discord.ButtonStyle.primary
        )
        view.add_item(button)
        
        # Send the embed with the button
        try:
            await channel.send(embed=embed, view=view)
            return {"message": "Ticket embed sent successfully"}
        except Exception as e:
            logger.error(f"Failed to send ticket embed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to send ticket embed: {str(e)}")


# Discord Bot API Integration Cog
class ServerAPI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.server = None
        self.server_task = None

    async def start_server(self):
        try:
            api.include_router(APIRoutes(self.bot).router)
            self.config = uvicorn.Config("utils.api:api", port=5000, log_level="info", host="0.0.0.0")
            self.server = uvicorn.Server(self.config)
            await self.server.serve()
        except Exception as e:
            logger.error(f"Server error: {e}")
            await asyncio.sleep(5)
            self.server_task = asyncio.create_task(self.start_server())

    async def stop_server(self):
        try:
            if self.server:
                await self.server.shutdown()
            else:
                logger.info("Server was not running")
        except Exception as e:
            logger.error(f"Error stopping server: {e}")

    async def cog_load(self):
        self.server_task = asyncio.create_task(self.start_server())
        self.server_task.add_done_callback(self.server_error_handler)

    def server_error_handler(self, future: asyncio.Future):
        try:
            future.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Unhandled server error: {e}")
            self.server_task = asyncio.create_task(self.start_server())

    async def cog_unload(self):
        try:
            if self.server_task:
                self.server_task.cancel()
            await self.stop_server()
        except Exception as e:
            logger.error(f"Error during cog unload: {e}")


async def setup(bot: commands.Bot):
    """Add the ServerAPI cog to the bot."""
    try:
        await bot.add_cog(ServerAPI(bot))
    except Exception as e:
        logger.error(f"Error setting up ServerAPI cog: {e}")
