import os
import dotenv
import logging
import time

import aiohttp
import discord
from discord.ext import commands, tasks
from discord.utils import get, setup_logging

from DataBase.database import get_database_handler

from DataModel.Mongo.Schema.Settings import Settings

from Utility.utils import get_prefix
from Utility.Constants import *

dotenv.load_dotenv()
setup_logging(level=logging.INFO)

intents = discord.Intents.default()
intents.presences = False
intents.message_content = True
intents.members = True
intents.messages = True
intents.moderation = True
intents.bans = True

class Bot(commands.Bot):

    async def close(self):
        await self.db.close()
        await self.session.close()
        await super().close()


    async def is_owner(self, user) -> bool:
        if user.id in [
            1201129677457215558, #coding.nerd
        ]:
            return True
        
        return False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if os.getenv('DATABASE') == 'MONGO':
            self.db = get_database_handler('MONGO')
            self.db.connect()
            logging.info("Connected to MongoDB")

        elif os.getenv('DATABASE') == 'MYSQL':
            self.db = get_database_handler('MYSQL')
            self.db.connect()
            logging.info("Connected to MySQL")

        self.settings = Settings(self.db, 'settings')
            
        self.session = aiohttp.ClientSession()

    async def on_ready(self):
        logging.info(f'Logged in as {self.user} (ID: {self.user.id})')
        change_status.start()


bot = Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    intents=intents,
    help_command=None,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True)
)

DEBUG_SERVER = os.getenv('DEBUG_SERVER')
if DEBUG_SERVER:
    bot.debug_server = get(bot.guilds, id=int(DEBUG_SERVER))

SHARD_CHANNEL = os.getenv('SHARD_CHANNEL')
if SHARD_CHANNEL:
    bot.shard_channel = get(bot.get_all_channels(), id=int(SHARD_CHANNEL))

    @bot.event
    async def on_shard_ready(shard_id):
        embed = discord.Embed(
            title="Shard Connected",
            description=f"Shard ID `{shard_id}` connected successfully.",
            color=BLANK_COLOR
        )
        await bot.shard_channel.send(embed=embed)

    @bot.event
    async def on_shard_disconnect(shard_id):
        embed = discord.Embed(
            title="Shard Disconnected",
            description=f"Shard ID `{shard_id}` disconnected.",
            color=BLANK_COLOR
        )
        await bot.shard_channel.send(embed=embed)

    @bot.event
    async def on_shard_resumed(shard_id):
        embed = discord.Embed(
            title="Shard Resumed",
            description=f"Shard ID `{shard_id}` resumed.",
            color=BLANK_COLOR
        )
        await bot.shard_channel.send(embed=embed)

@bot.after_invoke
async def loggingCommand(ctx: commands.Context):
    logging.info(f"{ctx.author} used {ctx.command} in {ctx.guild}.")

@tasks.loop(hours=1)
async def change_status():
    await bot.wait_until_ready()
    logging.info("Changing status")
    status = "✨ /about | Cyni v7.4"
    await bot.change_presence(
        activity=discord.CustomActivity(name=status)
    )

up_time = time.time()


def run():
    bot.run(os.getenv('TOKEN'))

if __name__ == '__main__':
    run()