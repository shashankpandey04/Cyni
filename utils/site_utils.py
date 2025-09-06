import os
import requests
from dotenv import load_dotenv
from Database.Mongo import mongo_db

from functools import lru_cache

load_dotenv()

@lru_cache(maxsize=16)
def get_bot_guilds(api_url: str):
    try:
        response = requests.post(f"{api_url}/fetch_bot_guilds", headers=headers)
        if response.status_code == 200:
            return tuple(response.json())
        print(f"[{api_url}] Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[{api_url}] Exception: {e}")
    return ()

api_token = os.getenv("API_TOKEN", "default_api_token")

headers = {"Authorization": api_token}

CYNI_API_BASE_URL = os.getenv("CYNI_API_BASE_URL", "https://cyni-api.x6xkh0.easypanel.host")
CYNI_PREMIUM_API_URL = os.getenv("CYNI_PREMIUM_API_URL", "https://cyni-premium-api.x6xkh0.easypanel.host")

def get_api_url_for_guild(guild_id: str) -> str:
    premium_doc = mongo_db["premium"].find_one({"_id": guild_id})
    if premium_doc:
        return CYNI_PREMIUM_API_URL
    else:
        return CYNI_API_BASE_URL

def get_bot_guilds(api_url: str):
    try:
        response = requests.post(f"{api_url}/fetch_bot_guilds", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[{api_url}] Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[{api_url}] Exception: {e}")
    return []
    
def get_guild(guild_id):
    api_url = get_api_url_for_guild(guild_id)
    if not api_url:
        print(f"API URL for guild {guild_id} not found.")
        return None
    response = requests.post(f"{api_url}/fetch_guild", params={"guild_id": guild_id}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching guild {guild_id}: {response.status_code} - {response.text}")
        return None
    
def get_guild_member(guild_id, user_id):
    api_url = get_api_url_for_guild(guild_id)
    if not api_url:
        print(f"API URL for guild {guild_id} not found.")
        return None
    response = requests.post(
        f"{api_url}/fetch_guild_member",
        params={"guild_id": guild_id, "user_id": user_id},
        headers=headers,
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching member {user_id} in guild {guild_id}: {response.status_code} - {response.text}")
        return None

def check_permissions(guild_id, user_id):
    guild = get_guild(guild_id)
    member = get_guild_member(guild_id, user_id)
    if not guild or not member:
        return False
    settings = mongo_db["settings"].find_one({"_id": int(guild_id)})
    has_permission = False
    if member.get("is_admin") or member.get("is_owner") or member.get("is_manage_guild"):
        has_permission = True
    else:
        user_roles = set(member.get("roles", []))
        management_roles = set(settings.get("basic_settings", {}).get("management_roles", []))
        if user_roles.intersection(management_roles):
            has_permission = True
    return has_permission

def get_guild_channels(guild_id):
    api_url = get_api_url_for_guild(guild_id)
    if not api_url:
        print(f"API URL for guild {guild_id} not found.")
        return None
    response = requests.post(
        f"{api_url}/fetch_guild_channels",
        json={"guild_id": guild_id},
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching channels for guild {guild_id}: {response.status_code} - {response.text}")
        return None
    
def get_guild_roles(guild_id):
    api_url = get_api_url_for_guild(guild_id)
    if not api_url:
        print(f"API URL for guild {guild_id} not found.")
        return None
    response = requests.post(
        f"{api_url}/fetch_guild_roles",
        json={"guild_id": guild_id},
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching roles for guild {guild_id}: {response.status_code} - {response.text}")
        return None
    
def get_guild_members(guild_id):
    api_url = get_api_url_for_guild(guild_id)
    if not api_url:
        print(f"API URL for guild {guild_id} not found.")
        return None
    
    response = requests.post(
        f"{api_url}/fetch_guild_members",
        json={"guild_id": guild_id},
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching members for guild {guild_id}: {response.status_code} - {response.text}")
        return None
    
def get_guild_categories(guild_id):
    api_url = get_api_url_for_guild(guild_id)
    if not api_url:
        print(f"API URL for guild {guild_id} not found.")
        return None
    response = requests.post(
        f"{api_url}/fetch_guild_categories",
        json={"guild_id": guild_id},
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching categories for guild {guild_id}: {response.status_code} - {response.text}")
        return None
    
def get_guild_emojis(guild_id):
    api_url = get_api_url_for_guild(guild_id)
    if not api_url:
        print(f"API URL for guild {guild_id} not found.")
        return None
    response = requests.post(
        f"{api_url}/fetch_guild_emojis",
        json={"guild_id": guild_id},
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching emojis for guild {guild_id}: {response.status_code} - {response.text}")
        return None