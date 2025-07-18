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

from utils.prc_api import PRC_API_Client
from decouple import config

from Datamodels.Settings import Settings
from Datamodels.Analytics import Analytics
from Datamodels.Warning import Warnings
from Datamodels.StaffActivity import StaffActivity
from Datamodels.Errors import Errors
from Datamodels.Sessions import Sessions
from Datamodels.Infraction_log import Infraction_log
from Datamodels.Infraction_types import Infraction_type
from Datamodels.Giveaway import Giveaway
from Datamodels.Backup import Backup
from Datamodels.afk import AFK
from Datamodels.Applications import Applications
from Datamodels.Partnership import Partnership
from Datamodels.LOA import LOA
from Datamodels.voteTracker import voteTracker


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

class Bot(commands.AutoShardedBot):

    async def is_owner(self, user: User) -> bool:

        if user.id in [
            1201129677457215558, #coding.nerd
        ]:
            return True
        
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.mongo = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGO_URI'))
            self.db = self.mongo["cyni"] if os.getenv("PRODUCTION_TOKEN") else self.mongo["dev"]
            self.settings_document = Document(self.db, 'settings')
            self.analytics_document = Document(self.db, 'analytics')
            self.warnings_document = Document(self.db, 'warnings')
            self.actvity_document = Document(self.db, 'staff_activity')
            self.appeals_document = Document(self.db, 'ban_appeals')
            self.errors_document = Document(self.db, 'errors')
            self.sessions_document = Document(self.db, 'sessions')
            self.infraction_log_document = Document(self.db, 'infraction_log')
            self.infraction_types_document = Document(self.db, 'infraction_types')
            self.giveaway_document = Document(self.db, 'giveaways')
            self.backup_document = Document(self.db, 'backup')
            self.afk_document = Document(self.db,'afk')
            self.applications_document = Document(self.db, 'applications')
            self.partnership_document = Document(self.db, 'partnership')
            self.loa_document = Document(self.db, 'loa')
            self.erlc_document = Document(self.db, 'erlc')
            self.vote_tracker_document = voteTracker(self.db, 'vote_tracker')

    async def close(self):
        print('Closing...')
        await super().close()
        self.mongo.close()
        print('Closed!')

    async def setup_hook(self) -> None:

        self.settings = Settings(self.db, 'settings')
        self.analytics = Analytics(self.db, 'analytics')
        self.warnings = Warnings(self.db, 'warnings')
        self.staff_activity = StaffActivity(self.db, 'staff_activity')
        self.ban_appeals = Document(self.db, 'ban_appeals')
        self.errors = Errors(self.db, 'errors')
        self.sessions = Sessions(self.db, 'sessions')
        self.infraction_log = Infraction_log(self.db, 'infraction_log')
        self.infraction_types = Infraction_type(self.db, 'infraction_types')
        self.giveaways = Giveaway(self.db, 'giveaways')
        self.backup = Backup(self.db, 'backup')
        self.afk = AFK(self.db,'afk')
        self.prc_api = PRC_API_Client(self, base_url=config('PRC_API_URL'), api_key=config('PRC_API_KEY'))
        self.applications = Applications(self.db, 'applications')
        self.partnership = Partnership(self.db, 'partnership')
        self.loa = LOA(self.db, 'loa')
        self.erlc = Document(self.db, 'erlc')
        self.vote_tracker = voteTracker(self.db, 'vote_tracker')
        
        Cogs = [m.name for m in iter_modules(['Cogs'],prefix='Cogs.')]
        Events = [m.name for m in iter_modules(['events'],prefix='events.')]
        EXT_EXTENSIONS = ["utils.api"]
        UNLOAD_EXTENSIONS = ["Cogs.Tickets", "Cogs.Applications", "Cogs.ERLC"]
        DISCONTINUED_EXTENSIONS = ["Cogs.Backup", "Cogs.YouTube"]


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

        logging.info("Loaded all extensions.")

        logging.info("Connected to MongoDB")

        change_status.start()
        loa_check.start(self)
        giveaway_roll.start(self)
        vote_track.start(self)

        logging.info(f"Logged in as {bot.user}")

        await bot.tree.sync()


bot = Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    intents=intents,
    help_command=None,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
    shard_count=3  # Manually manage for now
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

class PremiumRequired(commands.CheckFailure):
    def __init__(self, message="=This server doesn't have Cyni Premium!"):
        self.message = message
        super().__init__(self.message)

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

async def premium_check(bot, guild):
    guild_settings = await bot.settings.get(guild.id)
    if guild_settings:
        try:
            if "premium" in guild_settings.keys():
                if guild_settings['premium']['enabled']:
                    return True
        except KeyError:
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

async def fetch_invite(guild_id):
    guild = bot.get_guild(guild_id)
    if not guild:
        raise ValueError("Guild not found.")
    
    try:
        invite = await guild.vanity_invite()
        return invite.url
    except discord.Forbidden:
        pass

    try:
        invites = await guild.invites()
        if invites:
            return invites[0].url
    except discord.Forbidden:
        pass

    try:
        invite = await guild.text_channels[0].create_invite()
        return invite.url
    except discord.Forbidden:
        raise ValueError("Failed to get invite")

def is_premium():
    async def predicate(ctx):
        if await premium_check(ctx.bot, ctx.guild):
            return True
        raise PremiumRequired()
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
    try:
        bot.run(bot_token)
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    run()