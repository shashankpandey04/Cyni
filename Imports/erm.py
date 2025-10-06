import discord
from discord.ext import commands
import re
import json
import os
from dotenv import load_dotenv
from snowflake import SnowflakeGenerator
from collections import defaultdict

load_dotenv()

# ==== CONFIGURATION ====
BOT_TOKEN = os.getenv("IMPORT_BOT_TOKEN")
TARGET_BOT_ID = 978662093408591912  # Bot's ID to scrape
GUILD_ID = 1161376205216415817      # Your server's ID

# ==== INITIALIZATION ====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

snowflake_generator = SnowflakeGenerator(192)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await scrape_guild()


async def scrape_guild():
    """Scrape all messages from TARGET_BOT_ID across all channels in the guild."""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Guild Not Found")
        return

    punishments = []
    channel_counts = defaultdict(int)  # count messages per channel

    print(f"📥 Starting scrape in guild: {guild.name}")

    for channel in guild.text_channels:
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                if not (message.author.bot and message.author.id == TARGET_BOT_ID):
                    continue

                channel_counts[channel.id] += 1

                if not message.embeds:
                    continue

                embed = message.embeds[0]

                # Extract fields
                moderator_info = None
                violator_info = None
                for field in embed.fields:
                    if field.name == "Moderator Information":
                        moderator_info = field.value
                    elif field.name == "Violator Information":
                        violator_info = field.value

                if not moderator_info or not violator_info:
                    continue

                # --- Extract moderator info ---
                mod_match = re.search(r"\*\*Moderator:\*\* <@!?(\d+)>", moderator_info)
                snowflake_match = re.search(r"\*\*Warning ID:\*\* `(\d+)`", moderator_info)
                reason_match = re.search(r"\*\*Reason:\*\* (.+)", moderator_info)
                time_match = re.search(r"\*\*Moderated At:\*\* <t:(\d+)>", moderator_info)

                moderator_id = int(mod_match.group(1)) if mod_match else None
                snowflake_id = int(snowflake_match.group(1)) if snowflake_match else None
                reason = reason_match.group(1) if reason_match else None
                timestamp = int(time_match.group(1)) if time_match else None

                moderator_name = None
                if moderator_id:
                    try:
                        moderator = await bot.fetch_user(moderator_id)
                        moderator_name = moderator.name
                    except:
                        moderator_name = "Unknown"

                # --- Extract violator info ---
                username_match = re.search(r"\*\*Username:\*\* (.+)", violator_info)
                user_id_match = re.search(r"\*\*User ID:\*\* `(\d+)`", violator_info)
                type_match = re.search(r"\*\*Punishment Type:\*\* (.+)", violator_info)
                until_match = re.search(r"\*\*Until:\*\* <t:(\d+)>", violator_info)

                user_name = username_match.group(1) if username_match else None
                user_id = int(user_id_match.group(1)) if user_id_match else None
                punishment_type = type_match.group(1) if type_match else None
                until_epoch = int(until_match.group(1)) if until_match else None

                doc = {
                    "moderator_id": moderator_id,
                    "moderator_name": moderator_name,
                    "user_id": user_id,
                    "user_name": user_name,
                    "guild_id": GUILD_ID,
                    "reason": reason,
                    "type": punishment_type.lower() if punishment_type else None,
                    "timestamp": timestamp,
                    "snowflake": snowflake_id
                    if snowflake_id
                    else next(snowflake_generator),
                    "until": until_epoch,
                    "channel_id": channel.id,
                    "channel_name": channel.name,
                }

                punishments.append(doc)

        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"⚠️ Skipped channel {channel.name}: {e}")

    print(f"🎉 Finished scraping guild! Found {len(punishments)} punishments.")

    # Save punishments
    with open("punishments.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(punishments, indent=4))

    # Find channel with most messages
    if channel_counts:
        top_channel_id = max(channel_counts, key=channel_counts.get)
        top_channel = guild.get_channel(top_channel_id)
        top_count = channel_counts[top_channel_id]
        print(f"🔥 Bot sent the most messages in #{top_channel.name}: {top_count}")
    else:
        print("❌ No messages found from the target bot.")

    # Send export file to your support channel
    SUPPORT_SERVER_CHANNEL_ID = 1160481880253140992
    channel_ticket = bot.get_channel(SUPPORT_SERVER_CHANNEL_ID)
    if channel_ticket:
        await channel_ticket.send(
            content=f"📑 Exported {len(punishments)} punishments.\n"
                    f"🔥 Most active channel: #{top_channel.name} ({top_count} messages)",
            file=discord.File("punishments.txt"),
        )

bot.run(BOT_TOKEN)
