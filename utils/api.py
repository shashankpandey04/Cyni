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
from cyni import cad_access_check, cad_administrator_check, cad_operator_check

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
    
    async def POST_loa_request(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Notify a user about their application status."""
        logger.debug("Received POST request for LOA request.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        user_id = json_data.get("user_id")
        guild_id = json_data.get("guild_id")
        loa_reason = json_data.get("loa_reason")
        loa_start = json_data.get("loa_start")
        loa_end = json_data.get("loa_end")

        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        member = guild.get_member(user_id)
        if not member:
            logger.error(f"User  not found for ID: {user_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="User  not found")

        doc = await db.settings.find_one({"_id": guild_id})
        if not doc:
            logger.error(f"Settings not found for guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Settings not found")
        loa_channel = guild.get_channel(doc.get("loa_channel",{}).get("channel", None))
        if loa_channel is None:
            logger.error(f"LOA channel not found in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="LOA channel not found")
        loa_start = datetime.datetime.strptime(loa_start, "%Y-%m-%d").timestamp()
        loa_end = datetime.datetime.strptime(loa_end, "%Y-%m-%d").timestamp()
        loa_doc = {
            "user_id": user_id,
            "guild_id": guild_id,
            "loa_reason": loa_reason,
            "loa_start": loa_start,
            "loa_end": loa_end,
            "status": "pending",
            "approved_by": None,
            "created_at": str(datetime.datetime.now()),
        }
        embed = discord.Embed(
            title="Leave of Absence Request",
            description=f"**{member.name}** has requested a leave of absence.",
            color=discord.Color.blurple(),
        )

        embed.add_field(name="Reason", value=loa_reason, inline=False)
        embed.add_field(name="Start Date", value=loa_start, inline=True)
        embed.add_field(name="End Date", value=loa_end, inline=True)
        embed.set_footer(text="Please review the request and take necessary actions.", icon_url=guild.icon.url if guild.icon else "")

        await loa_channel.send(embed=embed)
        logger.debug(f"Sent LOA request to {loa_channel.name}.")

        return {"message": "LOA request sent successfully."}

    async def POST_change_loa_status(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Change the status of a LOA request."""
        logger.debug("Received POST request to change LOA status.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        user_id = json_data.get("user_id")
        guild_id = json_data.get("guild_id")
        status = json_data.get("status")
        approved_by = json_data.get("approved_by")

        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        member = guild.get_member(user_id)
        if not member:
            logger.error(f"User  not found for ID: {user_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="User  not found")

        doc = await db.settings.find_one({"_id": guild_id})
        if not doc:
            logger.error(f"Settings not found for guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Settings not found")
        loa_channel = guild.get_channel(doc.get("loa_channel",{}).get("channel", None))
        if loa_channel is None:
            logger.error(f"LOA channel not found in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="LOA channel not found")
        loa_doc = await db.loa.find_one({"user_id": user_id, "guild_id": guild_id, "status": "pending"})
        if not loa_doc:
            logger.error(f"LOA request not found for user: {member.name}")
            raise HTTPException(status_code=404, detail="LOA request not found")
        if status == "approved":
            await db.loa.update_one({"user_id": user_id, "guild_id": guild_id, "status": "pending"}, {"$set": {"status": "approved", "approved_by": approved_by}})
            
            embed = discord.Embed(
                title=f"LOA Approved in {guild.name}",
                description=f"Your leave of absence request has been approved by {approved_by}.",
                color=discord.Color.green(),
            )
            await member.send(embed=embed)

        elif status == "rejected":
            await db.loa.update_one({"user_id": user_id, "guild_id": guild_id, "status": "pending"}, {"$set": {"status": "rejected", "approved_by": approved_by}})
            embed = discord.Embed(
                title=f"LOA Rejected in {guild.name}",
                description=f"Your leave of absence request has been rejected by {approved_by}.",
                color=discord.Color.red(),
            )
            #send message to user
            await member.send(embed=embed)

        return {"message": "LOA status updated successfully."}
    
    async def POST_create_cad_team(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Create a new CAD team."""
        logger.debug("Received POST request to create a new CAD team.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        team = CAD_Team(**json_data)
        guild = self.bot.get_guild(team.guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {team.guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        owner = guild.get_member(team.owner_id)
        if not owner:
            logger.error(f"Owner not found for ID: {team.owner_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Owner not found")
        
        cad_admin = await cad_administrator_check(self.bot, guild, owner)
        if not cad_admin:
            logger.error(f"User is not a CAD administrator in guild: {guild.name}")
            raise HTTPException(status_code=403, detail="You are not a CAD administrator.")

        team_data = {
            "guild_id": team.guild_id,
            "team": team.team,
            "owner_id": team.owner_id,
            "co_owners": team.co_owners if team.co_owners else [],
            "members": team.members if team.members else [],
            "pending_members": team.pending_members if team.pending_members else [],
            "blacklist": team.blacklist if team.blacklist else [],
            "icon_url": team.icon_url if team.icon_url else " ",
            "created_at": datetime.datetime.now().timestamp(),
        }

        await db.cad_teams.insert_one(team_data)
        return {"message": "CAD team created successfully."}
    
    async def POST_update_cad_team(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Update an existing CAD team."""
        logger.debug("Received POST request to update an existing CAD team.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        team = CAD_Team(**json_data)
        guild = self.bot.get_guild(team.guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {team.guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        owner = guild.get_member(team.owner_id)
        if not owner:
            logger.error(f"Owner not found for ID: {team.owner_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Owner not found")
        
        cad_admin = await cad_administrator_check(self.bot, guild, owner)
        if not cad_admin:
            logger.error(f"User is not a CAD administrator in guild: {guild.name}")
            raise HTTPException(status_code=403, detail="You are not a CAD administrator.")

        team_data = {
            "guild_id": team.guild_id,
            "team": team.team,
            "owner_id": team.owner_id,
            "co_owners": team.co_owners if team.co_owners else [],
            "members": team.members if team.members else [],
            "pending_members": team.pending_members if team.pending_members else [],
            "blacklist": team.blacklist if team.blacklist else [],
            "icon_url": team.icon_url if team.icon_url else " ",
            "created_at": team.created_at,
        }

        await db.cad_teams.update_one({"guild_id": team.guild_id, "team": team.team}, {"$set": team_data})
        return {"message": "CAD team updated successfully."}
    
    async def POST_delete_cad_team(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Delete an existing CAD team."""
        logger.debug("Received POST request to delete an existing CAD team.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        team = json_data.get("team")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        owner = guild.get_member(team.owner_id)
        if not owner:
            logger.error(f"Owner not found for ID: {team.owner_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Owner not found")
        
        cad_admin = await cad_administrator_check(self.bot, guild, owner)
        if not cad_admin:
            logger.error(f"User is not a CAD administrator in guild: {guild.name}")
            raise HTTPException(status_code=403, detail="You are not a CAD administrator.")

        await db.cad_teams.delete_one({"guild_id": guild_id, "team": team})
        return {"message": "CAD team deleted successfully."}
    
    async def POST_add_cad_member(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Add a member to a CAD team."""
        logger.debug("Received POST request to add a member to a CAD team.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        team = json_data.get("team")
        member_id = json_data.get("member_id")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        owner = guild.get_member(team.owner_id)
        if not owner:
            logger.error(f"Owner not found for ID: {team.owner_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Owner not found")
        
        cad_admin = await cad_administrator_check(self.bot, guild, owner)
        if not cad_admin:
            logger.error(f"User is not a CAD administrator in guild: {guild.name}")
            raise HTTPException(status_code=403, detail="You are not a CAD administrator.")

        team_doc = await db.cad_teams.find_one({"guild_id": guild_id, "team": team})
        if not team_doc:
            logger.error(f"CAD team not found for guild: {guild.name}")
            raise HTTPException(status_code=404, detail="CAD team not found")
        
        if member_id in team_doc.get("members", []):
            logger.error(f"Member already exists in CAD team: {team}")
            raise HTTPException(status_code=400, detail="Member already exists in CAD team.")
        
        await db.cad_teams.update_one({"guild_id": guild_id, "team": team}, {"$push": {"members": member_id}})
        return {"message": "Member added to CAD team successfully."}
    
    async def POST_remove_cad_member(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Remove a member from a CAD team."""
        logger.debug("Received POST request to remove a member from a CAD team.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        team = json_data.get("team")
        member_id = json_data.get("member_id")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        owner = guild.get_member(team.owner_id)
        if not owner:
            logger.error(f"Owner not found for ID: {team.owner_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Owner not found")
        
        cad_admin = await cad_administrator_check(self.bot, guild, owner)
        if not cad_admin:
            logger.error(f"User is not a CAD administrator in guild: {guild.name}")
            raise HTTPException(status_code=403, detail="You are not a CAD administrator.")

        team_doc = await db.cad_teams.find_one({"guild_id": guild_id, "team": team})
        if not team_doc:
            logger.error(f"CAD team not found for guild: {guild.name}")
            raise HTTPException(status_code=404, detail="CAD team not found")
        
        if member_id not in team_doc.get("members", []):
            logger.error(f"Member not found in CAD team: {team}")
            raise HTTPException(status_code=400, detail="Member not found in CAD team.")
        
        await db.cad_teams.update_one({"guild_id": guild_id, "team": team}, {"$pull": {"members": member_id}})
        return {"message": "Member removed from CAD team successfully."}
    
    async def POST_add_cad_co_owner(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Add a co-owner to a CAD team."""
        logger.debug("Received POST request to add a co-owner to a CAD team.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        team = json_data.get("team")
        co_owner_id = json_data.get("co_owner_id")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        owner = guild.get_member(team.owner_id)
        if not owner:
            logger.error(f"Owner not found for ID: {team.owner_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Owner not found")
        
        cad_admin = await cad_administrator_check(self.bot, guild, owner)
        if not cad_admin:
            logger.error(f"User is not a CAD administrator in guild: {guild.name}")
            raise HTTPException(status_code=403, detail="You are not a CAD administrator.")

        team_doc = await db.cad_teams.find_one({"guild_id": guild_id, "team": team})
        if not team_doc:
            logger.error(f"CAD team not found for guild: {guild.name}")
            raise HTTPException(status_code=404, detail="CAD team not found")
        
        if co_owner_id in team_doc.get("co_owners", []):
            logger.error(f"Co-owner already exists in CAD team: {team}")
            raise HTTPException(status_code=400, detail="Co-owner already exists in CAD team.")
        
        await db.cad_teams.update_one({"guild_id": guild_id, "team": team}, {"$push": {"co_owners": co_owner_id}})
        return {"message": "Co-owner added to CAD team successfully."}
    
    async def POST_remove_cad_co_owner(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Remove a co-owner from a CAD team."""
        logger.debug("Received POST request to remove a co-owner from a CAD team.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        team = json_data.get("team")
        co_owner_id = json_data.get("co_owner_id")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        owner = guild.get_member(team.owner_id)
        if not owner:
            logger.error(f"Owner not found for ID: {team.owner_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Owner not found")
        
        cad_admin = await cad_administrator_check(self.bot, guild, owner)
        if not cad_admin:
            logger.error(f"User is not a CAD administrator in guild: {guild.name}")
            raise HTTPException(status_code=403, detail="You are not a CAD administrator.")

        team_doc = await db.cad_teams.find_one({"guild_id": guild_id, "team": team})
        if not team_doc:
            logger.error(f"CAD team not found for guild: {guild.name}")
            raise HTTPException(status_code=404, detail="CAD team not found")
        
        if co_owner_id not in team_doc.get("co_owners", []):
            logger.error(f"Co-owner not found in CAD team: {team}")
            raise HTTPException(status_code=400, detail="Co-owner not found in CAD team.")
        
        await db.cad_teams.update_one({"guild_id": guild_id, "team": team}, {"$pull": {"co_owners": co_owner_id}})
        return {"message": "Co-owner removed from CAD team successfully."}
    
    async def POST_request_cad_team(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Request to join a CAD team."""
        logger.debug("Received POST request to join a CAD team.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        team = json_data.get("team")
        member_id = json_data.get("member_id")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        member = guild.get_member(member_id)
        if not member:
            logger.error(f"Member not found for ID: {member_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Member not found")
        
        team_doc = await db.cad_teams.find_one({"guild_id": guild_id, "team": team})
        if not team_doc:
            logger.error(f"CAD team not found for guild: {guild.name}")
            raise HTTPException(status_code=404, detail="CAD team not found")
        
        if member_id in team_doc.get("members", []):
            logger.error(f"Member already exists in CAD team: {team}")
            raise HTTPException(status_code=400, detail="Member already exists in CAD team.")
        
        if member_id in team_doc.get("pending_members", []):
            logger.error(f"Member already has a pending request in CAD team: {team}")
            raise HTTPException(status_code=400, detail="Member already has a pending request in CAD team.")
        
        await db.cad_teams.update_one({"guild_id": guild_id, "team": team}, {"$push": {"pending_members": member_id}})
        return {"message": "Request sent to join CAD team successfully."}

    async def POST_approve_cad_request(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Approve a request to join a CAD team."""
        logger.debug("Received POST request to approve a request to join a CAD team.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        team = json_data.get("team")
        member_id = json_data.get("member_id")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        owner = guild.get_member(team.owner_id)
        if not owner:
            logger.error(f"Owner not found for ID: {team.owner_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Owner not found")
        
        cad_admin = await cad_administrator_check(self.bot, guild, owner)
        if not cad_admin:
            logger.error(f"User is not a CAD administrator in guild: {guild.name}")
            raise HTTPException(status_code=403, detail="You are not a CAD administrator.")

        team_doc = await db.cad_teams.find_one({"guild_id": guild_id, "team": team})
        if not team_doc:
            logger.error(f"CAD team not found for guild: {guild.name}")
            raise HTTPException(status_code=404, detail="CAD team not found")
        
        if member_id not in team_doc.get("pending_members", []):
            logger.error(f"Member not found in pending requests for CAD team: {team}")
            raise HTTPException(status_code=400, detail="Member not found in pending requests.")
        
        await db.cad_teams.update_one({"guild_id": guild_id, "team": team}, {"$push": {"members": member_id}})
        await db.cad_teams.update_one({"guild_id": guild_id, "team": team}, {"$pull": {"pending_members": member_id}})
        return {"message": "Request approved successfully."}
    
    async def POST_reject_cad_request(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Reject a request to join a CAD team."""
        logger.debug("Received POST request to reject a request to join a CAD team.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        team = json_data.get("team")
        member_id = json_data.get("member_id")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        owner = guild.get_member(team.owner_id)
        if not owner:
            logger.error(f"Owner not found for ID: {team.owner_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Owner not found")
        
        cad_admin = await cad_administrator_check(self.bot, guild, owner)
        if not cad_admin:
            logger.error(f"User is not a CAD administrator in guild: {guild.name}")
            raise HTTPException(status_code=403, detail="You are not a CAD administrator.")

        team_doc = await db.cad_teams.find_one({"guild_id": guild_id, "team": team})
        if not team_doc:
            logger.error(f"CAD team not found for guild: {guild.name}")
            raise HTTPException(status_code=404, detail="CAD team not found")
        
        if member_id not in team_doc.get("pending_members", []):
            logger.error(f"Member not found in pending requests for CAD team: {team}")
            raise HTTPException(status_code=400, detail="Member not found in pending requests.")
        
        await db.cad_teams.update_one({"guild_id": guild_id, "team": team}, {"$pull": {"pending_members": member_id}})
        return {"message": "Request rejected successfully."}
    
    async def POST_cad_team_log_create(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Create a new CAD team log."""
        logger.debug("Received POST request to create a new CAD team log.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        log = CAD_Log(**json_data)
        guild = self.bot.get_guild(log.guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {log.guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        created_by = guild.get_member(log.created_by)
        if not created_by:
            logger.error(f"Staff member not found for ID: {log.owner_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Staff member not found")
        
        cad_access = await cad_access_check(self.bot, guild, created_by)
        if not cad_access:
            logger.error(f"Staff member does not have access to CAD in guild: {guild.name}")
            raise HTTPException(status_code=403, detail="Staff member does not have access to CAD.")

        cad_team = await db.cad_teams.find_one({"guild_id": log.guild_id, "team": log.team})
        if not cad_team:
            logger.error(f"CAD team not found for guild: {guild.name}")
            raise HTTPException(status_code=404, detail="CAD team not found")
        
        if log.owner_id not in cad_team.get("members", []):
            logger.error(f"Staff member is not part of the CAD team: {log.team}")
            raise HTTPException(status_code=403, detail="Staff member is not part of the CAD team.")

        log_data = {
            "guild_id": log.guild_id,
            "created_by": log.owner_id,
            "team": log.team,
            "punishment": log.punishment,
            "reason": log.reason,
            "created_at": datetime.datetime.now().timestamp(),
        }

        await db.cad_logs.insert_one(log_data)
        return {"message": "CAD team log created successfully."}
    
    async def POST_cad_team_log_delete(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Delete a CAD team log."""
        logger.debug("Received POST request to delete a CAD team log.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        team = json_data.get("team")
        log_id = json_data.get("log_id")
        created_by = json_data.get("created_by")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        created_by = guild.get_member(created_by)
        if not created_by:
            logger.error(f"Staff member not found for ID: {created_by} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Staff member not found")
        
        cad_access = await cad_access_check(self.bot, guild, created_by)
        if not cad_access:
            logger.error(f"Staff member does not have access to CAD in guild: {guild.name}")
            raise HTTPException(status_code=403, detail="Staff member does not have access to CAD.")

        await db.cad_logs.delete_one({
            "_id": log_id,
            "created_by": created_by.id
        })
        return {"message": "CAD team log deleted successfully."}
    

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
