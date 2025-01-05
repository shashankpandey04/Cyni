from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_session import Session
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import requests
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import datetime
import socket
import asyncio
from waitress import serve
from bson import ObjectId
from cyni import bot, fetch_invite

# Load environment variables
load_dotenv()

# Constants
DISCORD_API_BASE_URL = "https://discord.com/api"
OAUTH_SCOPE = "identify guilds"
MANAGE_MESSAGES_PERMISSION = 0x2000
ADMINISTRATOR_PERMISSION = 0x8

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# Configure Flask-Session
mongo_client = MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client["cyni"] if os.getenv("PRODUCTION_TOKEN") else mongo_client["dev"]
sessions_collection = mongo_db["sessions"]
app.config['SESSION_TYPE'] = 'mongodb'
app.config['SESSION_MONGODB'] = mongo_client
app.config['SESSION_MONGODB_DB'] = mongo_db.name
app.config['SESSION_USE_SIGNER'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=48)  # Set session lifetime to 48 hours
Session(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# User class
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# In-memory user storage
users = {}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# Routes
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    discord_login_url = (
        f"{DISCORD_API_BASE_URL}/oauth2/authorize?client_id={os.getenv('DISCORD_CLIENT_ID')}"
        f"&redirect_uri={os.getenv('DISCORD_REDIRECT_URI')}&response_type=code&scope={OAUTH_SCOPE}"
    )
    return redirect(discord_login_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Authorization code not found.", 400
    
    token_response = requests.post(f"{DISCORD_API_BASE_URL}/oauth2/token", data={
        "client_id": os.getenv("DISCORD_CLIENT_ID"),
        "client_secret": os.getenv("DISCORD_CLIENT_SECRET"),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": os.getenv("DISCORD_REDIRECT_URI"),
        "scope": OAUTH_SCOPE
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    
    if token_response.status_code != 200:
        return f"Failed to fetch token: {token_response.text}", 500

    token_json = token_response.json()
    access_token = token_json.get("access_token")
    if not access_token:
        return "Access token not found.", 500
    
    session["access_token"] = access_token
    session["refresh_token"] = token_json.get("refresh_token")

    user_response = requests.get(f"{DISCORD_API_BASE_URL}/users/@me", headers={
        "Authorization": f"Bearer {access_token}"
    })

    if user_response.status_code != 200:
        return f"Failed to fetch user: {user_response.text}", 500

    user_json = user_response.json()
    session["user_id"] = user_json["id"]
    session["username"] = user_json["username"]

    session.permanent = True

    if user_json["id"] not in users:
        users[user_json["id"]] = User(user_json["id"])
        login_user(users[user_json["id"]])

    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    session.clear()
    users.pop(user_id, None)
    if user_id:
        sessions_collection.update_one(
            {"_id": user_id},
            {"$set": {"logged_in": False}}
        )
    logout_user()
    return redirect(url_for("index"))

@app.route("/docs")
def docs():
    flash("Documentation coming soon.")
    return redirect(url_for("dashboard"))

@app.route('/giveaway/<message_id>', methods=["GET"])
def giveaway(message_id):
    giveaway = mongo_db["giveaways"].find_one({"message_id": int(message_id)})
    if not giveaway:
        flash("Giveaway not found.")
        return redirect(url_for("dashboard"))

    return render_template("active_giveaway.html", guild=guild, giveaway=giveaway)

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    username = session["username"]
    access_token = session["access_token"]
    
    guilds_response = requests.get(f"{DISCORD_API_BASE_URL}/users/@me/guilds", headers={
        "Authorization": f"Bearer {access_token}"
    })
    
    if guilds_response.status_code != 200:
        return f"Failed to fetch guilds: {guilds_response.text}", 500
    
    guilds_json = guilds_response.json()
    
    if not isinstance(guilds_json, list):
        return f"Unexpected response format: {guilds_json}", 500
    
    user_guilds = []
    bot_guild_ids = {str(guild.id) for guild in bot.guilds}

    for guild in guilds_json:
        permissions = guild.get("permissions", 0)
        has_manage_messages = (permissions & MANAGE_MESSAGES_PERMISSION) == MANAGE_MESSAGES_PERMISSION
        is_admin = (permissions & ADMINISTRATOR_PERMISSION) == ADMINISTRATOR_PERMISSION
        is_owner = guild.get("owner", False)
        bot_present = guild["id"] in bot_guild_ids

        if (has_manage_messages or is_admin or is_owner) and bot_present:
            user_guilds.append({
                "id": guild["id"],
                "name": guild["name"],
                "icon": guild["icon"],
                "owner": guild["owner"]
            })
    
    session["guilds"] = user_guilds
    return render_template("dashboard.html", user_id=user_id, username=username, user_guilds=user_guilds)

@app.route('/dashboard/<guild_id>', methods=["GET", "POST"])
@login_required
def guild(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return render_template("404.html"), 404
    
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        return "You do not have the required permissions to access this page.", 403
    
    return render_template("guild.html", guild=guild)

@app.route('/dashboard/<guild_id>/settings/basics', methods=["GET", "POST"])
@login_required
def guild_settings_basics(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.")
        return redirect(url_for("guild", guild_id=guild_id))
    
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        return "You do not have the required permissions to access this page.", 403
    
    guild_data = mongo_db["settings"].find_one({"_id": guild.id})

    roles = {role.id: role.name for role in guild.roles}

    if request.method == "POST":
        prefix = request.form.get("prefix")
        staff_roles = request.form.getlist("staff_roles")
        management_roles = request.form.getlist("management_roles")

        staff_roles = [int(role) for role in staff_roles]
        management_roles = [int(role) for role in management_roles]

        mongo_db["settings"].update_one(
            {"_id": guild.id },
            {
                "$set": {
                    "customization.prefix": prefix,
                    "basic_settings.staff_roles": staff_roles,
                    "basic_settings.management_roles": management_roles
                }
            }
        )
        flash("Settings updated successfully.")
        return redirect(url_for("guild_settings_basics", guild_id=guild_id))

    return render_template("guild_settings_basics.html", guild=guild, guild_data=guild_data, roles=roles)

@app.route('/dashboard/<guild_id>/settings/anti-ping', methods=["GET", "POST"])
@login_required
def anti_ping_settings(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.")
        return redirect(url_for("guild", guild_id=guild_id))
    
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        return "You do not have the required permissions to access this page.", 403
    
    guild_data = mongo_db["settings"].find_one({"_id": guild.id})
    roles = {role.id: role.name for role in guild.roles}
    if request.method == "POST":
        affected_roles = request.form.getlist("affected_roles")
        exempt_roles = request.form.getlist("exempt_roles")
        enabled = request.form.get("enabled") == "on" 

        affected_roles = [int(role) for role in affected_roles]
        exempt_roles = [int(role) for role in exempt_roles]

        mongo_db["settings"].update_one(
            {"_id": guild.id},
            {
                "$set": {
                    "anti_ping_module.affected_roles": affected_roles,
                    "anti_ping_module.exempt_roles": exempt_roles,
                    "anti_ping_module.enabled": enabled
                }
            }
        )
        flash("Anti-Ping settings updated successfully.")
        return redirect(url_for("anti_ping_settings", guild_id=guild_id))

    return render_template("anti_ping_settings.html", guild=guild, guild_data=guild_data, roles=roles)

@app.route('/dashboard/<guild_id>/settings/moderation', methods=["GET", "POST"])
@login_required
def moderation_settings(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.")
        return redirect(url_for("guild", guild_id=guild_id))
    
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        return "You do not have the required permissions to access this page.", 403
    
    guild_data = mongo_db["settings"].find_one({"_id": guild.id})

    channels = {channel.id: channel.name for channel in guild.channels}

    if request.method == "POST":
        enabled = request.form.get("enabled") == "on"
        mod_log_channel = request.form.get("mod_log_channel")
        ban_appeal_channel = request.form.get("ban_appeal_channel")
        audit_log_channel = request.form.get("audit_log_channel")

        mongo_db["settings"].update_one(
            {"_id": guild.id},
            {
                "$set": {
                    "moderation_module.enabled": enabled,
                    "moderation_module.mod_log_channel": int(mod_log_channel) if mod_log_channel else None,
                    "moderation_module.ban_appeal_channel": int(ban_appeal_channel) if ban_appeal_channel else None,
                    "moderation_module.audit_log": int(audit_log_channel) if audit_log_channel else None
                }
            }
        )
        flash("Moderation settings updated successfully.")
        return redirect(url_for("moderation_settings", guild_id=guild_id))

    return render_template("moderation_settings.html", guild=guild, guild_data=guild_data, channels=channels)

def run_production():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Server running on http://localhost:80 and http://{local_ip}:80")
    serve(app, host="0.0.0.0", port=80)

if __name__ == "__main__":
    run_production()