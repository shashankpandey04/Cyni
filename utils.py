import json
import os
from bs4 import BeautifulSoup
import wikipediaapi
from googlesearch import search
import requests
import traceback
import discord
import string
import random
import time
try:
    with open('warnings.json', 'r') as warnings_file:
        warnings = json.load(warnings_file)
except FileNotFoundError:
    warnings = {}

def save_data():
    with open('warnings.json', 'w') as warnings_file:
        json.dump(warnings, warnings_file, indent=4)

CONFIG_FILE = "server_config.json"

def load_config():
    """Load server configuration from server_config.json file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    file.close()
    return {}


def save_config(config):
    """Save server configuration to server_config.json file."""
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)
    file.close()

def get_server_config(guild_id):
    """Get server configuration for a specific guild."""
    config = load_config()
    return config.get(str(guild_id), {})

def update_server_config(guild_id, data):
    """Update server configuration for a specific guild."""
    config = load_config()
    config[str(guild_id)] = data
    save_config(config)

def create_or_get_server_config(guild_id):
    """Create or get server configuration for a specific guild."""
    config = get_server_config(guild_id)
    if not config:
        config = {
            "staff_roles": [],
            "management_role": [],
            "mod_log_channel": "null",
            "premium": "false",
            "report_channel": "null",
            "blocked_search": [],
            "anti_ping": "false",
            "anti_ping_roles":[],
            "bypass_anti_ping_roles":[],
            "loa_role": "null",
            "staff_management_channel": "null"
        }
        update_server_config(guild_id, config)
    return config

def get_staff_roles(guild_id):
    """Get staff roles for a specific guild."""
    config = load_config()
    return config.get(str(guild_id), {}).get("staff_roles", [])

def get_management_roles(guild_id):
    """Get management roles for a specific guild."""
    config = load_config()
    return config.get(str(guild_id), {}).get("management_role", [])

def get_next_case_number(guild_id, user_id):
    try:
        with open('warnings.json', 'r') as file:
            warnings = json.load(file)
            if guild_id in warnings and user_id in warnings[guild_id]:
                user_warnings = warnings[guild_id][user_id]
                existing_case_numbers = [warning['case_number'] for warning in user_warnings]
                if existing_case_numbers:
                    next_case_number = max(existing_case_numbers) + 1
                else:
                    next_case_number = 1
                user_warnings.append({
                    "case_number": next_case_number,
                    "reason": "New case reason",
                    "date": "Current date and time"
                })
                with open('warnings.json', 'w') as json_file:
                    json.dump(warnings, json_file, indent=4)
                return next_case_number
            else:
                warnings.setdefault(guild_id, {}).setdefault(user_id, [])
                warnings[guild_id][user_id].append({
                    "case_number": 1,
                    "reason": "New case reason",
                    "date": "Current date and time"
                })
                with open('warnings.json', 'w') as json_file:
                    json.dump(warnings, json_file, indent=4)
                return 1
    except FileNotFoundError:
        print("Error: warnings.json file not found.")
        return 1
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in warnings.json.")
        return 1
    
def modlogchannel(guild_id):
  """Get moderation log channel for a specific guild."""
  config = load_config()
  return config.get(str(guild_id), {}).get("mod_log_channel")

def cleanup_guild_data(bot):
    try:
        with open("server_config.json", "r") as file:
            server_config = json.load(file)
        bot_guild_ids = {guild.id for guild in bot.guilds}
        for guild_id_str in list(server_config.keys()):
            guild_id = int(guild_id_str)         
            if guild_id not in bot_guild_ids:
                print(f"Bot is not a member of the guild {guild_id}. Removing data from server_config.json.")
                del server_config[guild_id_str]
        with open("server_config.json", "w") as file:
            json.dump(server_config, file, indent=4)
    except Exception as e:
        print(f"An error occurred while cleaning up guild data: {e}")

def load_customcommand():
    try:
        with open('custom_commands.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_customcommand(config):
    with open('custom_commands.json', 'w') as f:
        json.dump(config, f, indent=4)

wiki_wiki = wikipediaapi.Wikipedia('english')

def search_api(topic):
    topic_lower = topic.lower()

    with open('data.json', 'r') as json_file:
        data = json.load(json_file)
        if topic_lower in data:
            topic_desc_key = f"{topic_lower}_desc_desc"
            return truncate_to_nearest_sentence(data[topic_lower][topic_desc_key][:500], 500)
    page_py = wiki_wiki.page(topic)
    if page_py.exists():
        return truncate_to_nearest_sentence(page_py.summary[:500], 500)
    time.sleep(2)
    google_results = list(search(f"{topic} site:wikipedia.org", num_results=1))
    if google_results:
        first_result = google_results[0]
        if first_result.startswith("https://en.wikipedia.org/"):
            return truncate_to_nearest_sentence("Result: " + get_wikipedia_data(first_result)[:1500], 1500)
        else:
            return {first_result}
    else:
        return "Sorry, no information found for this topic."

def get_wikipedia_data(url):
  try:
      response = requests.get(url)
      if response.status_code == 200:
          soup = BeautifulSoup(response.text, 'html.parser')
          content_div = soup.find('div', {'id': 'mw-content-text'})
          paragraphs = content_div.find_all('p')
          data = '\n'.join([p.get_text() for p in paragraphs])
          return data
      else:
          return f"Failed to retrieve data. Status code: {response.status_code}"
  except Exception as e:
      return f"Error: {str(e)}"

def truncate_to_nearest_sentence(data, max_length):
  if len(data) <= max_length:
      return data
  else:
      truncated_data = data[:max_length]
      last_period_index = truncated_data.rfind('.')

      if last_period_index != -1 and (len(truncated_data) - last_period_index) > 0:
          return truncated_data[:last_period_index + 1]
      else:
          return truncated_data

def list_custom_commands_embeds(interaction):
    config = load_customcommand()
    guild_id = str(interaction.guild.id)
    custom_commands = config.get(guild_id, {})
    if not custom_commands:
        return [discord.Embed(description="No custom commands found for this server.")]
    embeds = []
    for name, details in custom_commands.items():
        embed = discord.Embed(title=details.get('title', ''),description=details.get('description', ''), color=details.get('colour', discord.Color.default().value))
        image_url = details.get('image_url')
        if image_url:
            embed.set_image(url=image_url)
        embeds.append(embed)
    return embeds

def get_existing_uids(file_path='cerror.json'):
    try:
        with open(file_path, 'r') as file:
            errors = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        errors = []

    existing_uids = set(error['uid'] for error in errors)
    return existing_uids

def generate_error_uid(existing_uids):
    while True:
        error_uid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        full_uid = "err_" + error_uid
        if full_uid not in existing_uids:
            return full_uid

def log_error(file_path, error, error_uid):
    print(f"An error occurred - Error UID: {error_uid}")
    traceback.print_exception(type(error), error, error.__traceback__)
    
    try:
        with open(file_path, 'r') as file:
            errors = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        errors = []
    
    errors.append({
        'uid': error_uid,
        'message': str(error),
        'traceback': traceback.format_exc()
    })
    
    with open(file_path, 'w') as file:
        json.dump(errors, file, indent=2)
    
async def check_permissions(ctx, user):
    staff_roles = get_staff_roles(str(ctx.guild.id))
    management_roles = get_management_roles(str(ctx.guild.id))
    is_staff = any(role.id in staff_roles for role in user.roles)
    is_management = any(role.id in management_roles for role in user.roles)
    return is_staff or is_management

async def check_permissions_management(ctx, user):
    management_roles = get_management_roles(str(ctx.guild.id))
    is_management = any(role.id in management_roles for role in user.roles)
    return is_management

def fetch_random_joke():
    url = 'https://official-joke-api.appspot.com/jokes/random'
    response = requests.get(url)
    data = response.json()
    joke_setup = data['setup']
    joke_punchline = data['punchline']
    print(joke_setup)
    return f"{joke_setup}\n{joke_punchline}"