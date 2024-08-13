import discord
from discord.abc import User
from discord.ext import commands
from discord.ext import tasks
from utils.mongo import Document
import sentry_sdk

from pkgutil import iter_modules
import logging
import os
import time

from dotenv import load_dotenv
import motor.motor_asyncio
from utils.utils import get_prefix
from Modals.ban_appeal import BanAppealModal


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

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.members = True
intents.voice_states = True

discord.utils.setup_logging(level=logging.INFO)
logging.basicConfig(level=logging.INFO)

class Bot(commands.Bot):
    
    async def close(self):
        print('Closing...')
        await super().close()
        print('Closed!')

    async def is_owner(self, user: User) -> bool:

        if user.id == 1201129677457215558:
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
        
        Cogs = [m.name for m in iter_modules(['Cogs'],prefix='Cogs.')]
        Events = [m.name for m in iter_modules(['events'],prefix='events.')]

        for extension in Cogs:
            try:
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
    
        logging.info("Connected to MongoDB")

        change_status.start()

        logging.info(f"Logged in as {bot.user}")

        await bot.tree.sync()


bot = Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    intents=intents,
    help_command=None,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True)
)

bot.debug_server = [1152949579407442050]

afk_users = {}

@bot.event
async def on_ready():
    all_afk_users = await bot.afk.get_all()
    for user in all_afk_users:
        afk_users[user["_id"]] = user["reason"]

@bot.before_invoke
async def AutoDefer(ctx: commands.Context):
    analytics = await bot.analytics.find_by_id(
        ctx.command.full_parent_name + f"{ctx.command.name}"
    )
    if not analytics:
        await bot.analytics.insert(
            {
                "_id": ctx.command.full_parent_name + f"{ctx.command.name}",
                "uses": 1
            }
        )
    else:
        await bot.analytics.upsert(
            {
                "_id": ctx.command.full_parent_name + f"{ctx.command.name}",
                "uses": analytics["uses"] + 1
            }
        )

@bot.after_invoke
async def loggingCommand(ctx: commands.Context):
    logging.info(f"{ctx.author} used {ctx.command} in {ctx.guild}.")

@bot.tree.command()
async def banappeal(interaction: discord.Interaction):
    '''
    Appeal a ban.
    '''
    await interaction.response.send_modal(BanAppealModal(bot))

@tasks.loop(hours=1)
async def change_status():
    await bot.wait_until_ready()
    logging.info("Changing status")
    status = "✨ /about | Cyni v7.4"
    await bot.change_presence(
        activity=discord.CustomActivity(name=status)
    )

up_time = time.time()

class PremiumRequired(commands.CheckFailure):
    def __init__(self, message="<:declined:1268849944455024671> This server doesn't have Cyni Premium!"):
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
    if member.guild_permissions.administrator:
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
    if member.guild_permissions.administrator:
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

def is_premium():
    async def predicate(ctx):
        if await premium_check(ctx.bot, ctx.guild):
            return True
        raise PremiumRequired()
    return commands.check(predicate)

bot.cyni_team = {
    "coding.nerd {Creator}" : 1201129677457215558
}

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