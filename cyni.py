import discord
from discord.ext import tasks, commands
import sentry_sdk
import os
from dotenv import load_dotenv
import logging
import traceback
import aiohttp
import motor.motor_asyncio
from discord.utils import get, setup_logging
from pkgutil import iter_modules

import bcrypt

from Utility.utils import get_prefix

intents = discord.Intents.default()
intents.members = True
intents.presences = False
intents.message_content = True

load_dotenv()

KEY = os.getenv("KEY")
ENV = os.getenv("ENV", "DEVELOPMENT")
TOKEN = os.getenv("TOKEN")


setup_logging(level=logging.INFO)

sentry_sdk.init(os.getenv("SENTRY_DSN"))

class Bot(commands.AutoShardedBot):

    async def close(self):
        await logging.warning("Closing bot")
        await self.session.close()
        await self.mongo_client.close()
        await super().close()

    async def is_owner(self, user):
        if user.id in [
            1201129677457215558, #coding.nerd
            707064490826530888, #imlimiteds
        ]:
            return True
        
        return False
    
    async def on_ready(self):
        logging.info(f"Logged in as {self.user} ({self.user.id})")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.db = self.mongo_client["cyni"] if ENV == "PRODUCTION" else self.mongo_client["cyni_dev"]
        logging.info(f"Connected to MongoDB with ENV {ENV}")
        self.session = aiohttp.ClientSession()
        
        self.load_extension("jishaku")

        Commands = [m.name for m in iter_modules(["Commands"])]
        Events = [m.name for m in iter_modules(["Events"])]
        API = [m.name for m in iter_modules(["API"])]
        AI = [m.name for m in iter_modules(["AI"])]
        for command in Commands:
            self.load_extension(command)
        for event in Events:
            self.load_extension(event)
        for api in API:
            self.load_extension(api)
        for ai in AI:
            self.load_extension(ai)

        logging.info(f"Loaded {len(Commands)} commands, {len(Events)} events, {len(API)} API, and {len(AI)} AI modules")



bot = Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    intents=intents,
    help_command=None,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
    shard_count=1
)

debug_server = int(os.getenv("DEBUG_SERVER"))
shard_channel = int(os.getenv("SHARD_CHANNEL"))

afk_users = {}

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

def run():
    bot.run(TOKEN)


if __name__ == "__main__":
    run()