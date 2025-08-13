import discord
from discord.abc import User
from discord.ext import commands
from discord.ext import tasks
from utils.mongo import Document

from pkgutil import iter_modules
import logging
import os
import time

from dotenv import load_dotenv
import motor.motor_asyncio
from utils.utils import get_prefix

from Tasks.loa_check import loa_check
from Tasks.GiveawayRoll import giveaway_roll
from Tasks.Vote_Tracker import vote_track
from Tasks.itterate_prc_logs import setup_prc_logs_processor

from utils.prc_api import PRC_API_Client
from utils.emoji_controller import EmojiController

from decouple import config

from Views.Tickets import TicketView
from menu import LOARequest

# from Models.modai import ModerationModel

# Custom exceptions for premium checks
class PremiumCheckError(commands.CheckFailure):
    """Base exception for premium check failures"""
    pass

class UsePremiumBotError(PremiumCheckError):
    """Raised when a premium server tries to use a non-premium bot"""
    def __init__(self):
        super().__init__("This server has premium enabled. Please use the CYNI Premium bot to access this feature.")

class UseRegularBotError(PremiumCheckError):
    """Raised when a non-premium server tries to use a premium bot"""
    def __init__(self):
        super().__init__("This server is not premium enabled. Please use the regular CYNI bot instead of the premium bot.")

class NotPremiumError(PremiumCheckError):
    """Raised when a non-premium server tries to access premium features"""
    def __init__(self):
        super().__init__("This server is not premium enabled. Please upgrade to CYNI Premium to access this feature.")


load_dotenv()

intents = discord.Intents.default()
intents.presences = False
intents.message_content = True
intents.members = True
intents.messages = True
intents.moderation = True
intents.bans = True
intents.webhooks = True
intents.guilds = True

discord.utils.setup_logging(level=logging.INFO)

_version = "8.1.1"
class Bot(commands.AutoShardedBot):

    async def is_owner(self, user: User) -> bool:

        if user.id in [
            1201129677457215558, #coding.nerd
            707064490826530888, #imlimiteds
        ]:
            return True

    async def close(self):
        print('Closing...')
        try:
            if hasattr(self, 'prc_api') and self.prc_api:
                await self.prc_api.cog_unload()
            if hasattr(self, 'roblox') and self.roblox:
                if hasattr(self.roblox, 'close'):
                    await self.roblox.close()
        except Exception as e:
            print(f'Error closing API sessions: {e}')
        
        await super().close()
        self.mongo.close()
        print('Closed!')

    async def on_ready(self):
        categories = await self.ticket_categories.find({})
        for category in categories:
            guild = self.get_guild(int(category["guild_id"]))
            if not guild:
                continue

            self.add_view(TicketView(
                guild=guild,
                category_id=str(category["_id"]),
                category=category,
                logger=self.logger
            ))
            
        loa_requests = await self.loa.find({
            "accepted": False,
            "denied": False,
            "voided": False,
            "expired": False
        })

        for loa in loa_requests:
            self.add_view(
                LOARequest(
                    bot=self,
                    guild_id=int(loa["guild_id"]),
                    user_id=int(loa["user_id"]),
                    schema_id=str(loa["_id"])
                )
            )

        self.logger.info(f'Logged in as {self.user.name} ({self.user.id})')
        self.logger.info('------')

    async def setup_hook(self) -> None:
        self.is_premium = True if os.getenv("PREMIUM_TOKEN") else False
        self.mongo = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGO_URI'))
        self.db = self.mongo["cyni"] if os.getenv("PRODUCTION_TOKEN") or os.getenv("PREMIUM_TOKEN") else self.mongo["dev"]
        self.bot_version = _version
        self.settings = Document(self.db, 'settings')
        self.analytics = Document(self.db, 'analytics')
        self.warnings = Document(self.db, 'warnings')
        self.staff_activity = Document(self.db, 'staff_activity')
        self.ban_appeals = Document(self.db, 'ban_appeals')
        self.errors = Document(self.db, 'errors')
        self.sessions = Document(self.db, 'sessions')
        self.infraction_log = Document(self.db, 'infraction_log')
        self.infraction_types = Document(self.db, 'infraction_types')
        self.giveaways = Document(self.db, 'giveaways')
        self.backup = Document(self.db, 'backup')
        self.afk = Document(self.db, 'afk')
        self.prc_api = PRC_API_Client(self, base_url=config('PRC_API_URL'), api_key=config('PRC_API_KEY'))
        self.applications = Document(self.db, 'applications')
        self.partnership = Document(self.db, 'partnership')
        self.loa = Document(self.db, 'loa')
        self.erlc = Document(self.db, 'erlc')
        self.vote_tracker = Document(self.db, 'vote_tracker')
        self.premium = Document(self.db, 'premium')
        self.shift_types = Document(self.db, 'shift_types')
        self.ticket_categories = Document(self.db, 'ticket_categories')
        self.emoji = EmojiController(self)
        self.logger = logging.getLogger()
        await self.emoji.prefetch_emojis()

        Cogs = [m.name for m in iter_modules(['Cogs'],prefix='Cogs.')]
        Events = [m.name for m in iter_modules(['events'],prefix='events.')]
        EXT_EXTENSIONS = ["utils.api"]
        UNLOAD_EXTENSIONS = ["Cogs.Applications","Cogs.ShiftManager","Cogs.RobloxPunishments"]
        DISCONTINUED_EXTENSIONS = ["Cogs.Backup", "Cogs.YouTube", "Cogs.Verify"]


        for extension in EXT_EXTENSIONS:
            try:
                await self.load_extension(extension)
                logging.info(f'Loaded extension {extension}.')
            except Exception as e:
                logging.error(f'Failed to load extension {extension}.', exc_info=True)

        for extension in Cogs:
            try:
                if extension in DISCONTINUED_EXTENSIONS:
                    logging.info(f'Skipping loading of discontinued extension {extension}.')
                    continue
                await self.load_extension(extension)
                logging.info(f'Loaded extension {extension}.')
            except Exception as e:
                logging.error(f'Failed to load extension {extension}.', exc_info=True)

        for extension in Events:
            try:
                await self.load_extension(extension)
                logging.info(f'Loaded extension {extension}.')
            except Exception as e:
                logging.error(f'Failed to load extension {extension}.', exc_info=True)

        if os.getenv("PRODUCTION_TOKEN"):
            for extension in UNLOAD_EXTENSIONS:
                try:
                    await self.unload_extension(extension)
                    logging.info(f'Unloaded extension {extension}.')
                except Exception as e:
                    logging.error(f'Failed to unload extension {extension}.', exc_info=True)

        try:
            await bot.load_extension("utils.hot_reload")
            logging.info('Loaded hot reload extension.')
        except Exception as e:
            logging.error('Failed to load hot reload extension.', exc_info=True)

        logging.info("Loaded all extensions.")

        logging.info("Connected to MongoDB")

        change_status.start()
        loa_check.start(self)
        giveaway_roll.start(self)
        vote_track.start(self)
        setup_prc_logs_processor(self)

        logging.info(f"Logged in as {bot.user}")

        await bot.tree.sync()


bot = Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    intents=intents,
    help_command=None,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=True, users=True),
)

bot.debug_server = [1152949579407442050]
bot.shard_channel = 1203343926388330518
bot.error_channel_id = 1203343926388330518

afk_users = {}

@bot.before_invoke
async def AutoDefer(ctx: commands.Context):
    from datetime import datetime
    
    command_name = ctx.command.full_parent_name + f"{ctx.command.name}"
    current_month = datetime.now().strftime("%Y-%m")
    
    analytics = await bot.analytics.find_by_id(command_name)
    if not analytics:
        await bot.analytics.insert(
            {
                "_id": command_name,
                "uses": 1,
                "monthly_usage": {current_month: 1}
            }
        )
    else:
        monthly_usage = analytics.get("monthly_usage", {})
        monthly_usage[current_month] = monthly_usage.get(current_month, 0) + 1
        
        await bot.analytics.upsert(
            {
                "_id": command_name,
                "uses": analytics["uses"] + 1,
                "monthly_usage": monthly_usage
            }
        )

@bot.after_invoke
async def loggingCommand(ctx: commands.Context):
   logging.info(f"{ctx.author} used {ctx.command} in {ctx.guild}.")

@tasks.loop(hours=1)
async def change_status():
    await bot.wait_until_ready()
    logging.info("Changing status")
    guild_count = len(bot.guilds)
    status = "Watching over " + str(guild_count) + " servers"
    await bot.change_presence(
        activity=discord.CustomActivity(name=status)
    )

@bot.event
async def on_shard_ready(shard_id):
    logging.info(f"Shard {shard_id} is ready.")

up_time = time.time()

async def staff_check(bot,guild,member):
    if member.guild_permissions.administrator:
        return True
    guild_settings = await bot.settings.get(guild.id)
    if guild_settings:
        if "staff_roles" in guild_settings["basic_settings"].keys():
            if guild_settings["basic_settings"]["staff_roles"] != []:
                if isinstance(guild_settings["basic_settings"]["staff_roles"], list):
                    for role in guild_settings["basic_settings"]["staff_roles"]:
                        if role in [role.id for role in member.roles]:
                            return True
            elif isinstance(guild_settings["basic_settings"]["staff_roles"], int):
                if guild_settings["basic_settings"]["staff_roles"] in [role.id for role in member.roles]:
                    return True
    return False

async def management_check(bot,guild,member):
    if member.guild_permissions.administrator:
        return True
    guild_settings = await bot.settings.get(guild.id)
    if guild_settings:
        if "management_roles" in guild_settings["basic_settings"].keys():
            if guild_settings["basic_settings"]["management_roles"] != []:
                if isinstance(guild_settings["basic_settings"]["management_roles"], list):
                    for role in guild_settings["basic_settings"]["management_roles"]:
                        if role in [role.id for role in member.roles]:
                            return True
            elif isinstance(guild_settings["basic_settings"]["management_roles"], int):
                if guild_settings["basic_settings"]["management_roles"] in [role.id for role in member.roles]:
                    return True
    return False

async def staff_or_management_check(bot,guild,member):
    if member.guild_permissions.administrator:
        return True
    if await staff_check(bot,guild,member) or await management_check(bot,guild,member):
        return True
    return False

async def roblox_staff_check(bot, guild, member):
    """Check if member has Roblox staff permissions."""
    if member.guild_permissions.administrator:
        return True

    guild_settings = await bot.settings.get(guild.id)
    if guild_settings and "roblox" in guild_settings:
        if "staff_roles" in guild_settings["roblox"]:
            roblox_staff_roles = guild_settings["roblox"]["staff_roles"]
            if roblox_staff_roles:
                if isinstance(roblox_staff_roles, list):
                    for role in roblox_staff_roles:
                        if role in [r.id for r in member.roles]:
                            return True
                elif isinstance(roblox_staff_roles, int):
                    if roblox_staff_roles in [r.id for r in member.roles]:
                        return True
    return False

async def roblox_management_check(bot, guild, member):
    """Check if member has Roblox management permissions."""
    if member.guild_permissions.administrator:
        return True

    guild_settings = await bot.settings.get(guild.id)
    if guild_settings and "roblox" in guild_settings:
        if "management_roles" in guild_settings["roblox"]:
            roblox_management_roles = guild_settings["roblox"]["management_roles"]
            if roblox_management_roles:
                if isinstance(roblox_management_roles, list):
                    for role in roblox_management_roles:
                        if role in [r.id for r in member.roles]:
                            return True
                elif isinstance(roblox_management_roles, int):
                    if roblox_management_roles in [r.id for r in member.roles]:
                        return True
    return False

async def premium_check_fun(bot, guild):
    premium = await bot.premium.find_by_id(guild.id)
    if premium is not None:
        return True
    else:
        return False

def is_staff():
    async def predicate(ctx):
        if await staff_check(ctx.bot,ctx.guild,ctx.author):
            return True
        raise commands.MissingPermissions(["Staff"])
    return commands.check(predicate)

def is_management():
    async def predicate(ctx):
        if await management_check(ctx.bot,ctx.guild,ctx.author):
            return True
        raise commands.MissingPermissions(["Management"])
    return commands.check(predicate)

def is_staff_or_management():
    async def predicate(ctx):
        if await staff_or_management_check(ctx.bot,ctx.guild,ctx.author):
            return True
        raise commands.MissingPermissions(["Staff or Management"])
    return commands.check(predicate)

def is_roblox_staff():
    async def predicate(ctx):
        if await roblox_staff_check(ctx.bot, ctx.guild, ctx.author):
            return True
        raise commands.MissingPermissions(["Roblox Staff"])
    return commands.check(predicate)

def is_roblox_management():
    async def predicate(ctx):
        if await roblox_management_check(ctx.bot, ctx.guild, ctx.author):
            return True
        raise commands.MissingPermissions(["Roblox Management"])
    return commands.check(predicate)

def premium_check():
    """Decorator that only blocks premium servers using non-premium bots"""
    async def predicate(ctx):
        premium_status = await premium_check_fun(ctx.bot, ctx.guild)
        if premium_status == "not_premium_server":
            raise NotPremiumError()
        return True
    return commands.check(predicate)

def bot_ready():
    if bot.is_ready():
        return True
    return False

if os.getenv("PRODUCTION_TOKEN"):
    bot_token = os.getenv("PRODUCTION_TOKEN")
    logging.info("Production Token")
elif os.getenv("PREMIUM_TOKEN"):
    bot_token = os.getenv("PREMIUM_TOKEN")
    logging.info("Using Premium Token")
else:
    bot_token = os.getenv("DEV_TOKEN")
    logging.info("Using Development Token")

def run():
    """Run the bot with simple shutdown."""
    try:
        bot.run(bot_token)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, bot stopping...")
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    run()