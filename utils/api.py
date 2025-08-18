from bson import ObjectId
from fastapi import FastAPI, APIRouter, Header, HTTPException, Request, Depends
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
import motor.motor_asyncio

from Views.Tickets import TicketButton, TicketView

# Load the environment variables
load_dotenv()

logger = logging.getLogger(__name__)

api = FastAPI()

bot_token = os.getenv("PRODUCTION_TOKEN") or os.getenv("PREMIUM_TOKEN") or os.getenv("DEV_TOKEN")

mongo = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGO_URI'))
db = mongo["cyni"] if os.getenv("PRODUCTION_TOKEN") or os.getenv("PREMIUM_TOKEN") else mongo["dev"]

api_token = os.getenv("API_TOKEN", "default_api_token")

import logging

logging.basicConfig(level=logging.INFO)

class ApplicationStatus(BaseModel):
    guild_id: int
    user_id: int
    application_name: str
    new_status: str
    pass_role: int
    fail_role: int
    result_channel: int
    note: str | None = "Not provided."

class TicketEmbedRequest(BaseModel):
    guild_id: int
    category_id: str


async def validate_authorization(bot, token: str):
    """Validate the authorization token."""
    if token == api_token:
        return True
    return False


# API Routes
class APIRoutes:

    RATE_LIMIT_WINDOW = 1
    RATE_LIMIT_THRESHOLD = 10

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.router = APIRouter()
        self.request_times = []

        for attr in dir(self):
            if attr.startswith(("GET_", "POST_", "PATCH_", "DELETE_")) and not attr.startswith("_"):
                method = attr.split("_")[0]
                route = attr[len(method) + 1:]
                logger.info(f"Registering API route: {method.upper()} /{route}")
                self.router.add_api_route(
                    f"/{route}",
                    getattr(self, attr),
                    methods=[method.upper()],
                    dependencies=[Depends(self.check_rate_limit)] 
                )
    async def check_rate_limit(self, request: Request):
        now = datetime.datetime.now().timestamp()
        self.request_times = [t for t in self.request_times if now - t <= self.RATE_LIMIT_WINDOW]
        if len(self.request_times) >= self.RATE_LIMIT_THRESHOLD:
            raise HTTPException(status_code=429, detail="Too Many Requests (global rate limit)")
        self.request_times.append(now)

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

    async def POST_fetch_guild_roles(
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
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        roles = {role.id: role.name for role in guild.roles}
        return roles
    
    async def POST_fetch_guild_channels(
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
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        channels = {channel.id: channel.name for channel in guild.channels}
        return channels

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
        loa_id = json_data.get("id")
        status = json_data.get("status")
        type = json_data.get("type", "LOA").upper()
        if type not in ["LOA", "QA"]:
            return {"message": "Invalid type provided. Must be 'LOA' or 'QA'."}, 400
        expiry_time = json_data.get("expiry", None)

        if not user_id or not guild_id or not loa_id or not status:
            logger.error("Missing required parameters in request.")
            return {"message": "Missing required parameters"}, 400

        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            return {"message": "Guild not found"}, 404

        member = guild.get_member(user_id)
        if not member:
            member = await self.bot.fetch_user(user_id)
            if not member:
                logger.error(f"User not found for ID: {user_id} in guild: {guild.name}")
                return {"message": "User not found"}, 404

        loa_doc = await db.loa.find_one({"_id": ObjectId(loa_id), "user_id": user_id, "guild_id": guild_id})
        if not loa_doc:
            logger.error(f"LOA request not found for user: {member.name}")
            return {"message": "LOA request not found"}, 404
        if status == "accepted":
            embed = discord.Embed(
                title=f"{type} Notice | {guild.name}",
                description=f"Your {type} request has been accepted by the management team.\n**Expiry Time:** <t:{int(expiry_time)}:R>" if expiry_time else "No expiry time set.",
                color=discord.Color.green(),
            )
            await member.send(embed=embed)

        elif status == "denied":
            embed = discord.Embed(
                title=f"{type} Notice | {guild.name}",
                description=f"Your {type} request has been rejected.",
                color=discord.Color.red(),
            )
            await member.send(embed=embed)
        
        elif status == "expired":
            embed = discord.Embed(
                title=f"{type} Notice | {guild.name}",
                description=f"Your {type} request has expired.",
                color=discord.Color.orange(),
            )
            await member.send(embed=embed)
            await db.loa.update_one(
                {"_id": ObjectId(loa_id)},
                {"$set": {"expiry": int(datetime.datetime.now().timestamp())}}
            )

        elif status == "voided":
            embed = discord.Embed(
                title=f"{type} Notice | {guild.name}",
                description=f"Your {type} request has been voided.",
                color=discord.Color.grey(),
            )
            await member.send(embed=embed)
        
        else:
            return {"message": "Invalid status provided. Must be 'accepted', 'denied', 'expired', or 'voided'."}, 400

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

        if authorization != api_token:
            logger.warning("Invalid or expired authorization for user.")
            logger.info(f"Authorization token: {authorization}")
            logger.info(f"API token: {api_token}")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        category_id = json_data.get("category_id")
        
        if not guild_id or not category_id:
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        
        category = await db.ticket_categories.find_one({"_id": category_id, "guild_id": int(guild_id)})
        if not category:
            raise HTTPException(status_code=404, detail="Ticket category not found")
        
        channel = guild.get_channel(int(category.get("ticket_channel")))
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        embed = discord.Embed(
            title=category.get("embed", {}).get("title", "Support Ticket"),
            description=category.get("embed", {}).get("description", "Click the button below to create a ticket"),
            color=category.get("embed", {}).get("color", 0x5865F2)
        )
        
        if guild.icon:
            embed.set_footer(text=f"{guild.name}", icon_url=guild.icon.url)
        else:
            embed.set_footer(text=f"{guild.name}")

        view = TicketView(
            guild=guild,
            category_id=category_id,
            category=category,
            logger=logger
        )

        try:
            await channel.send(embed=embed, view=view)
            return {"message": "Ticket embed sent successfully"}
        except Exception as e:
            logger.error(f"Failed to send ticket embed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to send ticket embed: {str(e)}")
        
    async def POST_send_latest_audit_logs(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Send the latest audit logs of a server."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Invalid authorization")
        if not await validate_authorization(self.bot, authorization):
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")
        
        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        if not guild_id:
            raise HTTPException(status_code=400, detail="Guild ID not provided")
        
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        
        audit_logs = []
        async for entry in guild.audit_logs(limit=3):
            changes = {}
            if entry.changes:
                for attr_name, change in entry.changes.items():
                    changes[attr_name] = {"before": change.before, "after": change.after}
            
            audit_logs.append({
                "user": str(entry.user),
                "action": entry.action.name,
                "target": str(entry.target) if entry.target else None,
                "created_at": entry.created_at.isoformat(),
                "changes": changes
            })
        if not audit_logs:
            raise HTTPException(status_code=404, detail="No audit logs found for this guild")

    async def POST_notify_application_submission(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Send a notification to the guild about a new application submission."""
        logger.debug("Received POST request to notify guild about application submission.")
        
        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning(f"Invalid or expired authorization. Expected: {bot_token[:10]}..., Got: {authorization[:10] if authorization else 'None'}...")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        user_id = json_data.get("user_id")
        guild_id = json_data.get("guild_id")
        application_name = json_data.get("application_name")
        result_channel_id = json_data.get("result_channel_id")
        application_id = json_data.get("application_id")

        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        sett = await db.settings.find_one({"_id": guild.id})
        if not sett:
            logger.error(f"Settings not found for guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Settings not found")
        
        result_channel = guild.get_channel(result_channel_id)
        if not result_channel:
            logger.error(f"Result channel not found for ID: {result_channel_id}")
            raise HTTPException(status_code=404, detail="Result channel not found")

        embed = discord.Embed(
            title="New Application Submitted",
            description=f"<@{user_id}> has submitted an application for **{application_name}**.",
            color=0x2F3136
        )
        embed.add_field(name="Application Name", value=application_name, inline=False)
        
        view = discord.ui.View()
        url_button = discord.ui.Button(
            label="View Application", 
            url=f"https://cyni.quprdigital.tk/application/logs/{guild_id}/{application_id}/{user_id}",
            style=discord.ButtonStyle.url
        )
        view.add_item(url_button)

        try:
            await result_channel.send(embed=embed, view=view)
            logger.debug(f"Sent application notification to result channel: {result_channel.name}.")
            return {"message": "Application notification sent successfully"}
        except Exception as e:
            logger.error(f"Failed to send application notification: {e}")
            raise HTTPException(status_code=500, detail="Failed to send application notification")

    async def POST_bot_vote_notification(
        self,
        request: Request
    ):
        """Notify the bot about a vote on Top.gg."""
        logger.debug("Received POST request to notify bot about a vote.")
        
        json_data = await request.json()
        user_id = json_data.get("user")
        bot_id = json_data.get("bot")

        if not user_id or not bot_id:
            logger.error("User ID or Bot ID not provided in the request.")
            raise HTTPException(status_code=400, detail="User ID or Bot ID not provided")
        
        user_found = False
        user = self.bot.get_user(int(user_id))
        if user:
            user_found = True
        
        VOTER_ROLE_ID = 1209464266898407444
        
        message = f"🎉 <@{user_id}> voted for CYNI on Top.gg!\nhttps://top.gg/bot/1136945734399295538/vote"

        channel = self.bot.get_channel(1206244123837993000)
        if not channel:
            logger.error("Channel not found for ID: 1206244123837993000")
            raise HTTPException(status_code=404, detail="Channel not found")
        
        try:
            await channel.send(message)
            if user_found:
                guild = self.bot.get_guild(1152949579407442050)
                if guild:
                    member = self.bot.get_guild(1152949579407442050).get_member(int(user_id))
                    if member:
                        role = guild.get_role(VOTER_ROLE_ID)
                        if role and role not in member.roles:
                            await member.add_roles(role, reason="User voted for CYNI on Top.gg")
                            logger.debug(f"Added voter role to user: {member.name}.")
                            await db.votes.insert_one({
                                "user_id": user_id,
                                "voted_at": datetime.datetime.now().timestamp()
                            })
                        else:
                            logger.debug(f"User {member.name} already has the voter role or it does not exist.")
                    else:
                        logger.error(f"Member not found in guild: {guild.name} for user ID: {user_id}")
                else:
                    logger.error("Guild not found for ID: 1152949579407442050")
            logger.debug(f"Sent vote notification to channel: {channel.name}.")
        except Exception as e:
            logger.error(f"Failed to send vote notification: {e}")
            raise HTTPException(status_code=500, detail="Failed to send vote notification")

    async def POST_create_webhook(
            self,
            authorization: Annotated[str | None, Header()],
            request: Request
    ):
        """Create a webhook for a specific channel."""
        logger.debug("Received POST request to create a webhook.")

        if not authorization:
            logger.warning("Authorization header is missing.")
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if authorization != bot_token:
            logger.warning("Invalid or expired authorization for user.")
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")
        channel_id = json_data.get("channel_id")
        purpose = json_data.get("purpose", "Webhook for CYNI Bot")

        if not guild_id or not channel_id:
            logger.error("Guild ID or Channel ID not provided in the request.")
            raise HTTPException(status_code=400, detail="Guild ID or Channel ID not provided")
        
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild not found for ID: {guild_id}")
            raise HTTPException(status_code=404, detail="Guild not found")

        channel = guild.get_channel(channel_id)
        if not channel:
            logger.error(f"Channel not found for ID: {channel_id} in guild: {guild.name}")
            raise HTTPException(status_code=404, detail="Channel not found")

        try:
            webhooks = await channel.webhooks()
            for webhook in webhooks:
                if webhook.user and webhook.user.id == self.bot.user.id:
                    return {"message": "Webhook already exists", "url": webhook.url}
                else:
                    return {"message": "Webhook already exists but not owned by the bot", "url": webhook.url}

            webhook = await channel.create_webhook(name=f"{guild.name} | {purpose}", reason=f"Webhook created by {self.bot.user.name} for {purpose}")
        except discord.Forbidden:
            logger.error(f"Bot does not have permission to create webhooks in channel: {channel.name}")
            return {"message": "Failed to create webhook", "error": "Insufficient permissions"}
        except Exception as e:
            logger.error(f"Error creating webhook in channel: {channel.name} - {e}")
            return {"message": "Failed to create webhook", "error": str(e)}

        logger.debug(f"Created webhook in channel: {channel.name} with ID: {webhook.id}.")
        return {"message": "Webhook created successfully", "url": webhook.url}

    async def POST_fetch_guild(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Takes GuildID and returns discord.Guild object."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Invalid authorization")
        
        if not await validate_authorization(self.bot, authorization):
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        # Try to get guild_id from query params first, then from JSON body
        guild_id = request.query_params.get("guild_id")
        if not guild_id:
            try:
                json_data = await request.json()
                guild_id = json_data.get("guild_id")
            except Exception:
                guild_id = None

        if not guild_id:
            raise HTTPException(status_code=400, detail="Guild ID not provided")
        
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        logger.debug(f"Retrieved guild: {guild.name} with ID: {guild.id}.")
        return {
            "id": str(guild.id),
            "name": guild.name,
            "icon_url": guild.icon.url if guild.icon else None,
            "owner_id": str(guild.owner_id),
            "member_count": guild.member_count,
            "features": guild.features,
            "is_large": guild.large,
            "permissions": guild.me.guild_permissions.value,
            "premium_tier": guild.premium_tier,
            "premium_subscription_count": guild.premium_subscription_count,
            "created_at": guild.created_at.isoformat(),
            "description": guild.description if hasattr(guild, 'description') else None,
            "splash_url": guild.splash.url if guild.splash else None,
            "banner_url": guild.banner.url if guild.banner else None,
            "owner": {
                "id": str(guild.owner.id),
                "name": guild.owner.name,
                "discriminator": guild.owner.discriminator,
                "avatar_url": guild.owner.avatar.url if guild.owner.avatar else None
            }
        }
    
    async def POST_fetch_guild_members(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Takes GuildID and returns a list of members in the guild."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if not await validate_authorization(self.bot, authorization):
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        json_data = await request.json()
        guild_id = json_data.get("guild_id")

        if not guild_id:
            raise HTTPException(status_code=400, detail="Guild ID not provided")

        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")

        members = []
        for member in guild.members:
            members.append({
                "id": str(member.id),
                "name": member.name,
                "discriminator": member.discriminator,
                "avatar_url": member.avatar.url if member.avatar else None,
                "joined_at": member.joined_at,
                "roles": [str(role.id) for role in member.roles]
            })

        logger.debug(f"Retrieved members for guild: {guild.name} with ID: {guild.id}.")
        return {"members": members}
    
    async def POST_fetch_guild_member(
        self,
        authorization: Annotated[str | None, Header()],
        request: Request
    ):
        """Takes GuildID and returns a member in the guild, only if they have manage_guild or administrator permissions."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if not await validate_authorization(self.bot, authorization):
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        guild_id = request.query_params.get("guild_id")
        user_id = request.query_params.get("user_id")
        if not guild_id or not user_id:
            try:
                json_data = await request.json()
                guild_id = guild_id or json_data.get("guild_id")
                user_id = user_id or json_data.get("user_id")
            except Exception:
                pass

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not provided")

        if not guild_id:
            raise HTTPException(status_code=400, detail="Guild ID not provided")

        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")

        member = guild.get_member(int(user_id))
        if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
            return {"message": "Member not found or does not have the required permissions."}

        logger.debug(f"Retrieved member for guild: {guild.name} with ID: {guild.id}.")
        doc = {
            "id": str(member.id),
            "name": member.name,
            "discriminator": member.discriminator,
            "avatar_url": member.avatar.url if member.avatar else None,
            "joined_at": member.joined_at,
            "roles": [str(role.id) for role in member.roles],
            "is_admin": True if member.guild_permissions.administrator else False,
            "is_manage_guild": True if member.guild_permissions.manage_guild else False,
            "display_name": member.display_name
        }
        return doc
    
    async def POST_fetch_bot_guilds(
        self,
        authorization: Annotated[str, Header()]
    ):
        """Returns a list of guilds the bot is in."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if not await validate_authorization(self.bot, authorization):
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        guilds = self.bot.guilds
        if not guilds:
            logger.debug("Bot is not in any guilds.")
            return {}
        logger.debug({str(guild.id) for guild in guilds})
        return {str(guild.id) for guild in guilds}
    
    async def POST_report_ratelimit(
            self,
            authorization: Annotated[str | None, Header()],
            request: Request
    ):
        if not authorization:
            raise HTTPException(status_code=401, detail="Invalid authorization")

        if not await validate_authorization(self.bot, authorization):
            raise HTTPException(status_code=401, detail="Invalid or expired authorization.")

        data = await request.json()
        user_id = data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not provided")
        
        channel_id = 1405223711233146910
        embed = discord.Embed(
            title="Rate Limit Exceeded",
            description=f"User {user_id} has exceeded the rate limit.",
            color=discord.Color.red()
        )

        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)

        return {"message": "Rate limit event reported successfully"}

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
