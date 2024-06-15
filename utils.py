from datetime import datetime, timezone
import json
import requests
import traceback
import discord
import string
import random
import json

from datetime import datetime,timezone
from dateutil import parser

from db import mycon

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
            "staff_management_channel": "null",
            "infraction_channel": "null",
            "promotion_channel": "null",
            "prefix": "?",
            "application_channel": "null",
            "message_quota": 0
        }
        update_server_config(guild_id, config)
    return config

def modlogchannel(guild_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("SELECT mod_log_channel FROM server_config WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"An error occurred while getting mod log channel: {e}")
    finally:
        cursor.close()

def save_custom_command(config):
    try:
        if mycon.is_connected():
            cursor = mycon.cursor()
            for guild_id, commands in config.items():
                for command_name, details in commands.items():
                    title = details.get('title', '')
                    description = details.get('description', '')
                    color = details.get('colour', '')
                    image_url = details.get('image_url', '')
                    cursor.execute("INSERT INTO custom_commands (guild_id, command_name, title, description, color, image_url) VALUES (%s, %s, %s, %s, %s, %s)", (guild_id, command_name, title, description, color, image_url))
            mycon.commit()
    except Exception as e:
        print("Error while connecting to MySQL", e)
    finally:
        if 'connection' in locals() and mycon.is_connected():
            cursor.close()
            mycon.close()

def list_custom_commands_embeds(interaction):
    config = load_custom_command()
    guild_id = str(interaction.guild.id)
    custom_commands = config.get(guild_id, {})
    if not custom_commands:
        return [discord.Embed(description="No custom commands found for this server.")]
    embeds = []
    for name, details in custom_commands.items():
        color_value = details.get('colour', discord.Color.default().value)
        try:
            color = int(color_value)
        except ValueError:
            async def send_error_message():
                await interaction.channel.send("Invalid color value found in database.")
                await send_error_message()
            continue  
        embed = discord.Embed(title=details.get('title', ''), description=details.get('description', ''), color=color)
        image_url = details.get('image_url')
        if image_url:
            embed.set_image(url=image_url)
        embeds.append(embed)
    return embeds

'''
wiki_wiki = wikipediaapi.Wikipedia('english')

def search_api(topic):
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
'''
def load_custom_command():
    try:
        if mycon.is_connected():
            cursor = mycon.cursor(dictionary=True)
            cursor.execute("SELECT * FROM custom_commands where guild_id = %s", (guild_id))
            rows = cursor.fetchall()
            config = {}
            for row in rows:
                guild_id = str(row['guild_id'])
                command_name = row['command_name']
                title = row['title']
                description = row['description']
                color = row['color']
                image_url = row['image_url']
                if guild_id not in config:
                    config[guild_id] = {}
                config[guild_id][command_name] = {
                    "Command Name": command_name,
                    'title': title,
                    'description': description,
                    'colour': color,
                    'image_url': image_url
                }
            return config
    except Exception as e:
        print("Error while connecting to MySQL", e)
    finally:
        if 'connection' in locals() and mycon.is_connected():
            cursor.close()
    return {}

def generate_error_uid():
    while True:
        error_uid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        full_uid = "err_" + error_uid
        return full_uid

def log_error(error, error_uid):
    cursor = None  # Initialize cursor variable outside the try block
    try:
        cursor = mycon.cursor()
        traceback.print_exception(type(error), error, error.__traceback__)
        insert_query = "INSERT INTO error_logs (uid, message, traceback) VALUES (%s, %s, %s)"
        values = (error_uid, str(error), traceback.format_exc())
        cursor.execute(insert_query, values)
        mycon.commit()
    except Exception as e:
        print("Failed to log error:", e)
    finally:
        if cursor is not None:
            cursor.close() 

async def check_permissions(ctx, user):
    staff_roles = get_staff_roles(str(ctx.guild.id))
    management_roles = get_management_roles(str(ctx.guild.id))
    is_staff = any(role.id in staff_roles for role in user.roles)
    is_management = any(role.id in management_roles for role in user.roles)
    return is_staff or is_management

async def check_permissions_management(ctx, user):
    management_roles = get_management_roles(ctx.guild.id)
    is_management = any(role.id in management_roles for role in user.roles)
    return is_management

def fetch_random_joke():
    url = 'https://official-joke-api.appspot.com/jokes/random'
    response = requests.get(url)
    data = response.json()
    joke_setup = data['setup']
    joke_punchline = data['punchline']
    return f"{joke_setup}\n{joke_punchline}"

#MYSQL

def get_staff_roles(guild_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("SELECT staff_roles FROM server_config WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
        if result:
            staff_roles = json.loads(result[0]) if result[0] else []
            return staff_roles
        else:
            return []
    except Exception as e:
        print(f"An error occurred while getting staff roles: {e}")
    finally:
        cursor.close()

def get_management_roles(guild_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("SELECT management_roles FROM server_config WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
        if result:
            management_roles = json.loads(result[0]) if result[0] else []
            return management_roles
        else:
            return []
    except Exception as e:
        print(f"An error occurred while getting management roles: {e}")
    finally:
        cursor.close()

def get_staff_or_management_roles(guild_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("SELECT staff_roles, management_roles FROM server_config WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
        if result:
            staff_roles = json.loads(result[0]) if result[0] else []
            management_roles = json.loads(result[1]) if result[1] else []
            return staff_roles + management_roles  # Concatenate staff and management roles
        else:
            return []
    except Exception as e:
        print(f"An error occurred while getting staff or management roles: {e}")
    finally:
        cursor.close()
    
def save_management_roles(guild_id, management_roles):
    try:
        cursor = mycon.cursor()
        serialized_management_roles = json.dumps(management_roles)
        cursor = mycon.cursor()
        cursor.execute("INSERT INTO server_config (guild_id, management_roles) VALUES (%s, %s) ON DUPLICATE KEY UPDATE management_roles = VALUES(management_roles)", (guild_id, serialized_management_roles))
        mycon.commit()
    except Exception as e:
        print(f"An error occurred while saving management roles: {e}")
    finally:
        cursor.close()

def save_staff_roles(guild_id, staff_roles):
    try:
        cursor = mycon.cursor()
        serialized_staff_roles = json.dumps(staff_roles)
        cursor.execute("INSERT INTO server_config (guild_id, staff_roles) VALUES (%s, %s) ON DUPLICATE KEY UPDATE staff_roles = VALUES(staff_roles)", (guild_id, serialized_staff_roles))
        mycon.commit()
    except Exception as e:
        print(f"An error occurred while saving staff roles: {e}")
    finally:
        cursor.close()

def cleanup_guild_data(bot):
    try:
        cursor = mycon.cursor()
        cursor.execute("SELECT guild_id FROM server_config")
        stored_guild_ids = [row[0] for row in cursor.fetchall()]
        bot_guild_ids = {guild.id for guild in bot.guilds}
        for guild_id in stored_guild_ids:
            if guild_id not in bot_guild_ids:
                print(f"Bot is not a member of the guild {guild_id}. Removing data from server_config table.")
                cursor.execute("DELETE FROM server_config WHERE guild_id = %s", (guild_id,))
                mycon.commit()
    except Exception as e:
        print(f"An error occurred while cleaning up guild data: {e}")
    finally:
        cursor.close()

def load_config():
    """Load server configuration from server_config table in the MySQL database."""
    config = {}
    try:
        cursor = mycon.cursor()
        cursor.execute("SELECT * FROM server_config")
        rows = cursor.fetchall()
        for row in rows:
            guild_id = row[0]
            data = json.loads(row[1])
            config[str(guild_id)] = data
    except Exception as e:
        print(f"An error occurred while loading server configuration: {e}")
    finally:
        cursor.close()
    return config

def save_config(config):
    """Save server configuration to server_config table in the MySQL database."""
    try:
        cursor = mycon.cursor()
        for guild_id, data in config.items():
            serialized_data = json.dumps(data)
            cursor.execute("INSERT INTO server_config (guild_id, staff_roles, management_roles) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE staff_roles = VALUES(staff_roles), management_roles = VALUES(management_roles)", (guild_id, serialized_data['staff_roles'], serialized_data['management_roles']))
        mycon.commit()
    except Exception as e:
        print(f"An error occurred while saving server configuration: {e}")
    finally:
        cursor.close()

def get_server_config(guild_id):
    """Get server configuration for a specific guild."""
    try:
        cursor = mycon.cursor()
        cursor.execute("SELECT * FROM server_config WHERE guild_id = %s", (guild_id,))
        row = cursor.fetchone()
        if row:
            config = {
                "guild_id": row[0],
                "staff_roles": json.loads(row[1] or "[]"),
                "management_roles": json.loads(row[2] or "[]"),
                "mod_log_channel": row[3],
                "premium": row[4],
                "report_channel": row[5],
                "blocked_search": json.loads(row[6] or "[]"),
                "anti_ping": row[7],
                "anti_ping_roles": json.loads(row[8] or "[]"),
                "bypass_anti_ping_roles": json.loads(row[9] or "[]"),
                "loa_role": json.loads(row[10] or "[]"),
                "staff_management_channel": row[11],
                "infraction_channel": row[12],
                "promotion_channel": row[13],
                "prefix": row[14],
                "application_channel": row[15],
                "message_quota": row[16]
            }
            return config
        else:
            return {}
    except Exception as e:
        print(f"An error occurred while getting server configuration: {e}")
    finally:
        cursor.close()

def update_server_config(guild_id, data):
    """Update server configuration for a specific guild."""
    try:
        cursor = mycon.cursor()
        serialized_data = json.dumps(data)
        try:
            cursor.execute("INSERT INTO server_config (guild_id, config_data) VALUES (%s, %s) ON DUPLICATE KEY UPDATE config_data = VALUES(config_data)", (guild_id, serialized_data))
            mycon.commit()
        except Exception as e:
            pass
    except Exception as e:
        print(f"An error occurred while updating server configuration: {e}")
    finally:
        cursor.close()

def save_mod_log_channel(guild_id, mod_log_channel_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("INSERT INTO server_config (guild_id, mod_log_channel) VALUES (%s, %s) ON DUPLICATE KEY UPDATE mod_log_channel = VALUES(mod_log_channel)", (guild_id, mod_log_channel_id))
        mycon.commit()
    except Exception as e:
        print(f"An error occurred while saving mod log channel: {e}")
    finally:
        cursor.close()

def set_anti_ping_option(guild_id, enable):
    try:
        cursor = mycon.cursor()
        cursor.execute("INSERT INTO server_config (guild_id, anti_ping) VALUES (%s, %s) ON DUPLICATE KEY UPDATE anti_ping = VALUES(anti_ping)", (guild_id, enable))
        mycon.commit()
    except Exception as e:
        print(f"An error occurred while setting anti-ping option: {e}")
    finally:
        cursor.close()
    
def save_anti_ping_roles(guild_id, anti_ping_roles):
    try:
        cursor = mycon.cursor()
        cursor.execute("INSERT INTO server_config (guild_id, anti_ping_roles) VALUES (%s, %s) ON DUPLICATE KEY UPDATE anti_ping_roles = VALUES(anti_ping_roles)", (guild_id, json.dumps(anti_ping_roles)))
        mycon.commit()
    except Exception as e:
        print(f"An error occurred while saving anti-ping roles: {e}")
    finally:
        cursor.close()

def save_anti_ping_bypass_roles(guild_id, anti_ping_bypass_roles):
    try:
        cursor = mycon.cursor()
        cursor.execute("INSERT INTO server_config (guild_id, bypass_anti_ping_roles) VALUES (%s, %s) ON DUPLICATE KEY UPDATE bypass_anti_ping_roles = VALUES(bypass_anti_ping_roles)", (guild_id, json.dumps(anti_ping_bypass_roles)))
        mycon.commit()
    except Exception as e:
        print(f"An error occurred while saving anti-ping bypass roles: {e}")
    finally:
        cursor.close()

def save_loa_roles(guild_id, loa_roles):
    try:
        cursor = mycon.cursor()
        cursor.execute("INSERT INTO server_config (guild_id, loa_role) VALUES (%s, %s) ON DUPLICATE KEY UPDATE loa_role = VALUES(loa_role)", (guild_id, json.dumps(loa_roles)))
        mycon.commit()
    except Exception as e:
        print(f"An error occurred while saving LOA roles: {e}")
    finally:
        cursor.close()

def save_staff_management_channel(guild_id, staff_management_channel_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("INSERT INTO server_config (guild_id, staff_management_channel) VALUES (%s, %s) ON DUPLICATE KEY UPDATE staff_management_channel = VALUES(staff_management_channel)", (guild_id, staff_management_channel_id))
        mycon.commit()
    except Exception as e:
        print(f"An error occurred while saving staff management channel: {e}")
    finally:
        cursor.close()

def robloxusername(userid):
    api_url = f"https://users.roblox.com/v1/users/{userid}"
    avatar_api_url = f"https://www.roblox.com/avatar-thumbnails?params=[{{userId:{userid}}}]"
    response = requests.get(avatar_api_url)
    avatar_data = response.json()[0]
    thumbnail_url = avatar_data["thumbnailUrl"]
    response = requests.get(api_url)
    data = response.json()
    created_timestamp = datetime.strptime(data["created"], "%Y-%m-%dT%H:%M:%S.%fZ")
    created_unix_timestamp = int(created_timestamp.timestamp())
    created_str = f"<t:{created_unix_timestamp}:R>"
    embed = discord.Embed(title="User Info", color=0x2F3136)
    embed.add_field(name="User ID", value=data["id"], inline=True)
    embed.add_field(name="Username", value=data["name"], inline=True)
    embed.add_field(name="Display Name",value=data["displayName"],inline=True)
    embed.add_field(name="Description",value=data["description"],inline=True)
    embed.set_thumbnail(url=thumbnail_url)
    embed.add_field(name="Is Banned", value=data["isBanned"], inline=True)
    embed.add_field(name="Has Verified Badge",value=data["hasVerifiemyconadge"],inline=True)
    embed.add_field(name="Created", value=created_str, inline=True)
    return embed

def generate_variations(word):
    variations = []
    substitutions = {
        'a': '@',
        'A': '@',
        'e': '3',
        'i': '1',
        'I': '1',
        'o': '0',
        's': '$'
    }
    for char in word:
        if char.lower() in substitutions:
            for sub in substitutions[char.lower()]:
                variation = word[:word.index(char)] + sub + word[word.index(char) + 1:]
                variations.append(variation)
    return variations

            
def save_promotion_channel(guild_id,channel_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("INSERT INTO server_config (guild_id, promotion_channel) VALUES (%s, %s) ON DUPLICATE KEY UPDATE promotion_channel = VALUES(promotion_channel)", (guild_id, channel_id))
        mycon.commit()
    except Exception as e:
        print(f"An error occurred while saving LOA roles: {e}")
    finally:
        cursor.close()

def save_infraction_channel(guild_id,channel_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("INSERT INTO server_config (guild_id, infraction_channel) VALUES (%s, %s) ON DUPLICATE KEY UPDATE infraction_channel = VALUES(infraction_channel)", (guild_id, channel_id))
        mycon.commit()
    except Exception as e:
        print(f"An error occurred while saving LOA roles: {e}")
    finally:
        cursor.close()

def get_promo_channel(guild_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("SELECT promotion_channel FROM server_config WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"An error occurred while getting promotion channel: {e}")
    finally:
        cursor.close()

def get_infraction_channel(guild_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("SELECT infraction_channel FROM server_config WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"An error occurred while getting infraction channel: {e}")
    finally:
        cursor.close()

def save_application_channel(guild_id,channel_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("INSERT INTO server_config (guild_id, application_channel) VALUES (%s, %s) ON DUPLICATE KEY UPDATE application_channel = VALUES(application_channel)", (guild_id, channel_id))
        mycon.commit()
    except Exception as e:
        print(f"An error occurred while saving LOA roles: {e}")
    finally:
        cursor.close()

def get_application_channel(guild_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("SELECT application_channel FROM server_config WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"An error occurred while getting application channel: {e}")
    finally:
        cursor.close()

def save_message_quota(guild_id, quota):
    try:
        # Insert or update message quota
        cursor = mycon.cursor()
        query = """
        INSERT INTO server_config (guild_id, message_quota)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE message_quota = VALUES(message_quota)
        """
        cursor.execute(query, (guild_id, quota))
        mycon.commit() 
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()

def get_message_quota(guild_id):
    try:
        cursor = mycon.cursor()
        cursor.execute("SELECT message_quota FROM server_config WHERE guild_id = %s", (guild_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"An error occurred while getting message quota: {e}")
    finally:
        cursor.close()

async def submit_ban_appeal(bot, interaction, date, reason, how, guild_id):
    try:
        guild = bot.get_guild(guild_id)
        if guild is None:
            guild = await bot.fetch_guild(guild_id)
        if guild is None:
            await interaction.response.send_message("The guild does not exist.")
            return

        banned_users = []
        async for entry in guild.bans():
            banned_users.append(entry.user.id)
        
        if interaction.user.id not in banned_users:
            await interaction.response.send_message("You are not banned from this server.")
            return
        if interaction.user.id == guild.owner_id:
            await interaction.response.send_message("The server owner cannot submit a ban appeal.")
            return
        # Fetch the application channel using the guild ID
        application_channel_id = get_application_channel(guild_id)
        
        if application_channel_id:
            application_channel_id = int(application_channel_id)

            # Fetch the channel using the bot's API, since interaction.guild is not used
            channel = bot.get_channel(application_channel_id)
            if channel is None:
                channel = await bot.fetch_channel(application_channel_id)

            cursor = mycon.cursor()
            cursor.execute("SELECT * FROM ban_appeals WHERE user_id = %s AND guild_id = %s AND status = 'pending'", (interaction.user.id, guild_id))
            result = cursor.fetchone()
            if result:
                await interaction.response.send_message("You already have a pending ban appeal.")
                return
            cursor.execute("INSERT INTO ban_appeals (user_id, guild_id, date, reason, how, status) VALUES (%s, %s, %s, %s, %s, %s)", (interaction.user.id, guild_id, date, reason, how, 'pending'))
            mycon.commit()
            cursor.close()

            if channel:
                embed = discord.Embed(title="Ban Appeal", color=0x2F3136)
                embed.add_field(name="Date Of Ban", value=date, inline=False)
                embed.add_field(name="Reason For Ban", value=reason, inline=False)
                embed.add_field(name="How You Will Change", value=how, inline=False)
                embed.add_field(name="User", value=interaction.user.mention, inline=True)
                embed.add_field(name="User ID", value=interaction.user.id, inline=True)
                await channel.send(embed=embed)
                await interaction.response.send_message("Your Ban Appeal has been submitted.")
            else:
                await interaction.response.send_message("The application channel is not set up. The server owner has been notified.")
                owner = await bot.fetch_user(guild_id)
                await owner.send("The application channel is not set up. Please set it up to receive ban appeals.")
        else:
            await interaction.response.send_message("The application channel is not set up.")
    except Exception as e:
        print(f"An error occurred while submitting the ban appeal: {e}")
        await interaction.response.send_message("An error occurred while submitting the ban appeal.")

def check_support_role(bot, member):
    support_server = bot.get_guild(1152949579407442050)
    support_role = support_server.get_role(1152949579407442050)
    return support_role in member.roles

def discord_timestamp(dt):
    """
    Converts a datetime object to Discord timestamp format.

    Parameters:
    dt (datetime): The datetime object to convert.

    Returns:
    str: Discord timestamp format string.
    """
    # Convert datetime to UTC and format as ISO 8601
    discord_timestamp = dt.replace(tzinfo=timezone.utc).isoformat()

    return f"<t:{int(dt.timestamp())}:F>"

def roblox_discord_timestamp(iso_str):
    """
    Converts an ISO 8601 date-time string to Discord timestamp format.

    Parameters:
    iso_str (str): The ISO 8601 date-time string to convert.

    Returns:
    str: Discord timestamp format string.
    """
    # Parse the ISO 8601 date-time string
    dt = parser.isoparse(iso_str)
    
    # Ensure the datetime is in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    # Convert datetime to UNIX timestamp and format as Discord timestamp
    unix_timestamp = int(dt.timestamp())

    return f"<t:{unix_timestamp}:F>"