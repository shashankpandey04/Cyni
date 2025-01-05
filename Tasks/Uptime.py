from discord.ext import tasks
import requests
import pymongo
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["cyni"] if os.getenv("PRODUCTION_TOKEN") else client['dev']
uptime_collection = db["uptime"]

bot_link = 'https://cyni.quprdigital.tk/uptime/bot'
website_link = 'https://cyni.quprdigital.tk'
erlc_api = 'https://api.policeroleplay.community/v1/server'

def check_website_status(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return "up"
        else:
            return "down"
    except requests.exceptions.RequestException as e:
        print(f"Error checking {url}: {e}")
        return "down"

def calculate_uptime_percentage(service_name):
    thirty_days_ago = datetime.now() - timedelta(days=30)
    thirty_days_ago_timestamp = thirty_days_ago.timestamp()

    records = list(uptime_collection.find({
        "service_name": service_name,
        "timestamp": {"$gte": thirty_days_ago_timestamp}
    }))

    total_checks = len(records)
    up_count = sum(1 for record in records if record["status"] == "up")

    if total_checks == 0:
        return 0

    uptime_percentage = (up_count / total_checks) * 100
    return uptime_percentage

@tasks.loop(minutes=5)
async def check_uptime():
    """
    Checks the uptime of all the websites and records the status.
    """
    bot_status = check_website_status(bot_link)
    website_status = check_website_status(website_link)
    erlc_status = check_website_status(erlc_api)

    timestamp = datetime.now().timestamp()

    bot_uptime_percentage = calculate_uptime_percentage("Bot")
    website_uptime_percentage = calculate_uptime_percentage("Website")
    erlc_uptime_percentage = calculate_uptime_percentage("ERLC API")

    uptime_collection.insert_one({
        "service_name": "Bot",
        "status": bot_status,
        "timestamp": timestamp,
        'uptime_percentage': bot_uptime_percentage
    })

    uptime_collection.insert_one({
        "service_name": "Website",
        "status": website_status,
        "timestamp": timestamp,
        'uptime_percentage': website_uptime_percentage
    })

    uptime_collection.insert_one({
        "service_name": "ERLC API",
        "status": erlc_status,
        "timestamp": timestamp,
        'uptime_percentage': erlc_uptime_percentage
    })

    print(f"Checked uptime at {timestamp}: Bot is {bot_status}, Website is {website_status}, ERLC API is {erlc_status}")

    thirty_days_ago = datetime.now() - timedelta(days=30)
    thirty_days_ago_timestamp = thirty_days_ago.timestamp()
    uptime_collection.delete_many({"timestamp": {"$lt": thirty_days_ago_timestamp}})

    print("Deleted old records.")


async def start_uptime_check():
    check_uptime.start()
