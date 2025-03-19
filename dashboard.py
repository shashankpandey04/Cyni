from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from flask_session import Session
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import requests
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import datetime
import uuid
from functools import wraps
from waitress import serve
from bson import ObjectId, Int64
from cyni import bot, fetch_invite, bot_ready
from utils.erm_api import *

from DashboardModules.WelcomeModule import welcome_route

# Load environment variables
load_dotenv()

# Constants
DISCORD_API_BASE_URL = "https://discord.com/api"
OAUTH_SCOPE = "identify guilds"
MANAGE_MESSAGES_PERMISSION = 0x2000
ADMINISTRATOR_PERMISSION = 0x8

ERM_API_BASE_URL = "https://core.ermbot.xyz/"

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
Session(app)

# Register Blueprint
app.register_blueprint(welcome_route)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Logged in successfully."
login_manager.login_message_category = "info"

bot_token = os.getenv("PRODUCTION_TOKEN") if os.getenv("PRODUCTION_TOKEN") else os.getenv("DEV_TOKEN")

# User class
class User(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_id(self):
        return self.id

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
    session['next'] = request.args.get('next', '/dashboard')
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

    next_url = session.pop('next', '/dashboard')
    return redirect(next_url)

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
    flash("Documentation coming soon.", "info")
    return redirect(url_for("index"))

@app.route('/giveaway/<message_id>', methods=["GET"])
def giveaway(message_id):
    giveaway = mongo_db["giveaways"].find_one({"message_id": int(message_id)})
    if not giveaway:
        flash("Giveaway not found.")
        return redirect(url_for("dashboard"))

    return render_template("active_giveaway.html", guild=guild, giveaway=giveaway)

@app.route('/status', methods=["GET"])
def status():
    website_link = 'https://cyni.quprdigital.tk'
    erlc_api = 'https://api.policeroleplay.community/v1/server'
    bot = bot_ready()
    website = requests.get(website_link)
    if website.status_code == 200:
        website = True
    else:
        website = False
    erlc = requests.get(erlc_api)
    if erlc.status_code == 403:
        erlc = True
    else:
        erlc = False
    return render_template("status.html", bot=bot, website=website, erlc=erlc)


@app.route("/dashboard")
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

    official_guild_id = '1152949579407442050'
    affiliated_guild_ids = list(mongo_db['affiliated_guilds'].find())

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
                "owner": guild["owner"],
                "official": True if guild["id"] == official_guild_id else False,
                "affiliated": True if guild["id"] in affiliated_guild_ids else False,
                "admin": is_admin,
                "moderator": has_manage_messages
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
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    
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

    guild_data = mongo_db["settings"].find_one({"_id": guild.id}) or {}

    customization = guild_data.get("customization", {})
    prefix = customization.get("prefix", "?")
    basic_settings = guild_data.get("basic_settings", {})
    staff_roles = basic_settings.get("staff_roles", [])
    management_roles = basic_settings.get("management_roles", [])

    roles = {role.id: role.name for role in guild.roles}

    if request.method == "POST":
        prefix = request.form.get("prefix")
        staff_roles = request.form.getlist("staff_roles")
        management_roles = request.form.getlist("management_roles")

        staff_roles = [int(role) for role in staff_roles]
        management_roles = [int(role) for role in management_roles]

        mongo_db["settings"].update_one(
            {"_id": guild.id},
            {
                "$set": {
                    "customization.prefix": prefix,
                    "basic_settings.staff_roles": staff_roles,
                    "basic_settings.management_roles": management_roles
                }
            },
            upsert=True
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
    
    guild_data = mongo_db["settings"].find_one({"_id": guild.id}) or {}

    anti_ping_module = guild_data.get("anti_ping_module", {})
    affected_roles = anti_ping_module.get("affected_roles", [])
    exempt_roles = anti_ping_module.get("exempt_roles", [])
    enabled = anti_ping_module.get("enabled", False)
    
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
            },
            upsert=True
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
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    
    guild_data = mongo_db["settings"].find_one({"_id": guild.id}) or {}

    moderation_module = guild_data.get("moderation_module", {})
    enabled = moderation_module.get("enabled", False)
    mod_log_channel = moderation_module.get("mod_log_channel", None)
    ban_appeal_channel = moderation_module.get("ban_appeal_channel", None)
    audit_log_channel = moderation_module.get("audit_log", None)

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
            },
            upsert=True
        )
        flash("Moderation settings updated successfully.")
        return redirect(url_for("moderation_settings", guild_id=guild_id))

    return render_template("moderation_settings.html", guild=guild, guild_data=guild_data, channels=channels)

@app.route('/applications/manage/<guild_id>', methods=["GET"])
@login_required
def applications(guild_id):
    if request.method == "GET":
        guild = bot.get_guild(int(guild_id))
        if not guild:
            flash("Guild not found.", "error")
            return redirect(url_for("dashboard"))
        sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
        management_roles = sett.get("basic_settings", {}).get("management_roles", [])
        if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles
                   if management_roles) or not (guild.get_member(int(session["user_id"])).guild_permissions.manage_guild or guild.get_member(int(session["user_id"])).guild_permissions.administrator):
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("dashboard"))
        all_applications = list(mongo_db["applications"].find())
        return render_template("applications.html", applications=all_applications, guild=guild)
    
@app.route('/applications/manage/<guild_id>/create', methods=["POST","GET"])
@login_required
def create_application(guild_id):
    if request.method == "GET":
        guild = bot.get_guild(int(guild_id))
        if not guild:
            flash("Guild not found.", "error")
            return redirect(url_for("dashboard"))
        sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
        management_roles = sett.get("basic_settings", {}).get("management_roles", [])
        if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles
                     if management_roles) or not (guild.get_member(int(session["user_id"])).guild_permissions.manage_guild or guild.get_member(int(session["user_id"])).guild_permissions.administrator):
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("dashboard"))
        return render_template("create_application.html", guild=guild)

    elif request.method == "POST":
        if current_user.is_authenticated:
            guild = bot.get_guild(int(guild_id))
            if not guild:
                flash("Guild not found.", "error")
                return redirect(url_for("dashboard"))
            
            sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
            management_roles = sett.get("basic_settings", {}).get("management_roles", [])
            if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles):
                flash("You do not have the required permissions to access this page.", "error")
                return redirect(url_for("dashboard"))
            
            application_name = request.form.get("application_name")
            application_description = request.form.get("application_description")
            required_roles = [int(role) for role in request.form.getlist("required_roles")]
            application_channel = int(request.form.get("application_channel"))
            all_questions = request.form.getlist("question")
            pass_role = int(request.form.get("pass_role"))
            fail_role = int(request.form.get("fail_role"))

            application_data = {
                "guild_id": int(guild_id),
                "name": application_name,
                "description": application_description,
                "required_roles": required_roles,
                "questions": [{"question": question} for question in all_questions],
                "application_channel": application_channel,
                "pass_role": pass_role,
                "fail_role": fail_role,
                "status": "open",
                "created_at": datetime.now().timestamp()
            }

            mongo_db["applications"].insert_one(application_data)
            flash("Application created successfully.")
            return redirect(url_for("applications", guild_id=guild_id))
    
@app.route('/applications/manage/<guild_id>/<application_id>', methods=["GET", "POST"])
@login_required
def manage_application(guild_id, application_id):
    if request.method == "GET":
        guild = bot.get_guild(int(guild_id))
        if not guild:
            flash("Guild not found.", "error")
            return redirect(url_for("applications", guild_id=guild_id))
        sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
        management_roles = sett.get("basic_settings", {}).get("management_roles", [])

        if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles):
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("applications", guild_id=guild_id))
        
        application = mongo_db["applications"].find_one({"_id": ObjectId(application_id)})
        if not application:
            flash("Application not found.", "error")
            return redirect(url_for("applications", guild_id=guild_id))
        return render_template("manage_application.html", guild=guild, application=application)
    
    if request.method == "POST":
        application_name = request.form.get("application_name")
        application_description = request.form.get("application_description")
        required_roles = [int(role) for role in request.form.getlist("required_roles")]
        application_channel = int(request.form.get("application_channel"))
        all_questions = request.form.getlist("question")
        pass_role = int(request.form.get("pass_role"))
        fail_role = int(request.form.get("fail_role"))
        status = request.form.get("status")

        application_data = {
            "guild_id": int(guild_id),
            "name": application_name,
            "description": application_description,
            "required_roles": required_roles,
            "questions": [{"question": question} for question in all_questions],
            "application_channel": application_channel,
            "pass_role": pass_role,
            "fail_role": fail_role,
            "status": status,
        }

        mongo_db["applications"].update_one(
            {"_id": ObjectId(application_id)},
            {"$set": application_data}
        )

        flash("Application updated successfully.")
        return redirect(url_for("applications", guild_id=guild_id))

@app.route('/applications/apply/<guild_id>/<application_id>', methods=["GET", "POST"])
@login_required
def apply(guild_id, application_id):
    if request.method == "GET":
        guild = bot.get_guild(int(guild_id))
        if not guild:
            flash("Guild not found.", "error")
            return redirect(url_for("dashboard"))
        application = mongo_db["applications"].find_one({"_id": ObjectId(application_id)})
        if not application:
            flash("Application not found.", "error")
            return redirect(url_for("applications", guild_id=guild_id))
        
        member = guild.get_member(int(session["user_id"]))
        if not member:
            flash("You are not a member of this guild.", "error")
            return redirect(url_for("dashboard"))

        required_roles = application.get("required_roles", [])
        if not any(role in [role.id for role in member.roles] for role in required_roles):
            flash("You do not have the required roles to apply.", "error")
            return redirect(url_for("dashboard"))

        existing_application = mongo_db["user_applications"].find_one({
            "user_id": session["user_id"],
            "application_id": application_id,
            "status": "pending"
        })
        if existing_application:
            flash("You have already applied for this application.", "error")
            return redirect(url_for("dashboard"))
        
        return render_template("apply.html", guild=guild, application=application)
    
    if request.method == "POST":
        application = mongo_db["applications"].find_one({"_id": ObjectId(application_id)})
        if not application:
            flash("Application not found.", "error")
            return redirect(url_for("applications", guild_id=guild_id))
        
        member = bot.get_guild(int(guild_id)).get_member(int(session["user_id"]))
        if not member:
            flash("You are not a member of this guild.", "error")
            return redirect(url_for("dashboard"))
        
        existing_application = mongo_db["user_applications"].find_one({
            "user_id": session["user_id"],
            "application_id": application_id,
            "status": "pending"
        })
        if existing_application:
            flash("You have already applied for this application.", "error")
            return redirect(url_for("dashboard"))
        
        answers = [request.form.get(f"answer_{i}") for i in range(1, len(application["questions"]) + 1)]
        print(len(answers), len(application["questions"]))
        if len(answers) != len(application["questions"]):
            flash("Please answer all questions.", "error")
            return redirect(url_for("apply", guild_id=guild_id, application_id=application_id))
        
        application_data = {
            "guild_id": int(guild_id),
            "name": str(member.name),
            "user_id": str(member.id),
            "application_id": application_id,
            "application_name": application["name"],
            "answers": [{"answer": answer} for answer in answers],
            "status": "pending",
            "guild_id": int(guild_id),
            "created_at": datetime.now().timestamp()
        }
        data = {
            "guild_id": int(guild_id),
            "user_id": str(member.id),
            "application_name": application["name"],
            "application_channel": application["application_channel"]
        }
        headers = {"Authorization": bot_token}
        URL = 'http://127.0.0.1:5000/notify_application_submission'
        #response = requests.post(URL, headers=headers, json=data)
        mongo_db["user_applications"].insert_one(application_data)
        flash("Application submitted successfully.")
        return redirect(url_for("dashboard"))
    
@app.route('/applications/logs/<guild_id>', methods=["GET"])
@login_required
def application_logs(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))
    
    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    management_roles = sett.get("basic_settings", {}).get("management_roles", [])
    if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles):
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))

    user_applications = list(mongo_db["user_applications"].find(
        {"guild_id": int(guild_id)}
    ))

    return render_template("application_logs.html", guild=guild, user_applications=user_applications)

@app.route('/applications/logs/<guild_id>/<application_id>/<user_id>', methods=["GET", "POST"])
@login_required
def user_application(guild_id, application_id, user_id):
    if request.method == "GET":
        guild = bot.get_guild(int(guild_id))
        if not guild:
            flash("Guild not found.", "error")
            return redirect(url_for("dashboard"))
        
        sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
        management_roles = sett.get("basic_settings", {}).get("management_roles", [])
        if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles):
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("dashboard"))
        
        application = mongo_db["applications"].find_one({"_id": ObjectId(application_id)})
        if not application:
            print("Application not found.")
            flash("Application not found.", "error")
            return redirect(url_for("applications", guild_id=guild_id))

        user_application = mongo_db["user_applications"].find_one({
            "guild_id": Int64(guild_id),
            "user_id": str(user_id),
            "application_id": str(application_id)
        })
        if not user_application:
            print("This user has not applied for this application.")
            flash("Application log not found.", "error")
            return redirect(url_for("application_logs", guild_id=guild_id))
        
        return render_template("user_application.html", guild=guild, application=application, user_application=user_application)
    
    if request.method == "POST":
        guild = bot.get_guild(int(guild_id))
        if not guild:
            flash("Guild not found.", "error")
            return redirect(url_for("dashboard"))
        
        sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
        management_roles = sett.get("basic_settings", {}).get("management_roles", [])
        if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles):
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("dashboard"))
        
        application = mongo_db["applications"].find_one({"_id": ObjectId(application_id)})
        if not application:
            flash("Application not found.", "error")
            return redirect(url_for("applications", guild_id=guild_id))
        
        user_application = mongo_db["user_applications"].find_one({
            "guild_id": Int64(guild_id),
            "user_id": str(user_id),
            "application_id": str(application_id)
        })
        if not user_application:
            flash("Application log not found.", "error")
            return redirect(url_for("application_logs", guild_id=guild_id))
        
        new_status = request.form.get("status")
        mongo_db["user_applications"].update_one(
            {"_id": user_application["_id"]},
            {"$set": {"status": new_status}}
        )

        data = {
            "guild_id": int(guild_id),
            "user_id": str(user_id),
            "application_name": application.get("name"),
            "new_status": new_status,
            "pass_role": application.get("pass_role"),
            "fail_role": application.get("fail_role"),
            "result_channel": application.get("application_channel"),
            "note": request.form.get("note")
        }
        headers = {"Authorization": bot_token}
        URL = 'http://127.0.0.1:5000/notify_user'
        response = requests.post(URL, headers=headers, json=data)

        if response.status_code == 200:
            flash("Application status updated successfully.")
        else:
            flash("Failed to notify user: " + response.json().get("error", "Unknown error"), "error")

        flash("Application status updated successfully.")
        return redirect(url_for("application_logs", guild_id=guild_id))

@app.route('/banappeal/manage/<guild_id>', methods=["GET", "POST"])
@login_required
def ban_appeal_manage(guild_id):
    if request.method == "GET":
        guild = bot.get_guild(int(guild_id))
        if not guild:
            flash("Guild not found.", "error")
            return redirect(url_for("dashboard"))
        
        sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
        management_roles = sett.get("basic_settings", {}).get("management_roles", [])
        if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles):
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("dashboard"))
        appeal_application = mongo_db["appeal_applications"].find_one({"guild_id": int(guild_id)})
        if not appeal_application:
            appeal_application = {
                "questions": [
                    {"question": "Why were you banned?"},
                    {"question": "Why should we unban you?"},
                    {"question": "What will you do to prevent this from happening again?"},
                    {"question": "Do you have any additional information to provide?"},
                    {"question": "Do you have any evidence to provide?"},
                ]
            }
        return render_template("ban_appeal_manage.html", guild=guild, appeal_application=appeal_application)
    
    if request.method == "POST":
        guild = bot.get_guild(int(guild_id))
        if not guild:
            flash("Guild not found.", "error")
            return redirect(url_for("dashboard"))
        
        management_roles = mongo_db["settings"].find_one({"_id": guild.id}).get("basic_settings", {}).get("management_roles", [])
        if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles):
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("dashboard"))

        questions = request.form.getlist("question")
        appeal_application = {
            "guild_id": int(guild_id),
            "questions": [{"question": question} for question in questions]
        }
        mongo_db["appeal_applications"].update_one(
            {"guild_id": int(guild_id)},
            {"$set": appeal_application},
            upsert=True
        )
        flash("Ban appeal application updated successfully.")
        return redirect(url_for("ban_appeal", guild_id=guild_id))

@app.route('/banappeal/apply/<guild_id>', methods=["GET", "POST"])
@login_required
def ban_appeal(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "GET":
        if mongo_db["ban_appeals"].find_one(
            {
                "guild_id": int(guild_id),
                "user_id": session["user_id"],
                "status": "pending"
                }
            ):
            flash("You have already appealed your ban.", "error")
            return redirect(url_for("dashboard"))

        appeal_application = mongo_db["appeal_applications"].find_one({"guild_id": int(guild_id)}) or {
            "questions": [
                {"question": "Why were you banned?"},
                {"question": "Why should we unban you?"},
                {"question": "What will you do to prevent this from happening again?"},
                {"question": "Do you have any additional information to provide?"},
                {"question": "Do you have any evidence to provide?"},
            ]
        }
        
        return render_template("ban_appeal.html", guild=guild, appeal_application=appeal_application)
    
    appeal_application = mongo_db["appeal_applications"].find_one({"guild_id": int(guild_id)})
    questions = [q['question'] for q in appeal_application["questions"]]
    answers = [request.form.get(f"answer_{i}") for i in range(1, len(questions) + 1)]

    if not all(answers):
        flash("Please answer all questions.", "error")
        return redirect(url_for('ban_appeal', guild_id=guild_id))

    uid = str(uuid.uuid4())
    while mongo_db["ban_appeals"].find_one({"appeal_id": uid}):
        uid = str(uuid.uuid4())

    appeal_data = {
        "appeal_id": uid,
        "guild_id": int(guild_id),
        "user_id": session["user_id"],
        "questions": [{"question": q, "answer": a} for q, a in zip(questions, answers)],
        "status": "pending",
        "timestamp": datetime.now(),
        "username": session["username"]
    }
    mongo_db["ban_appeals"].insert_one(appeal_data)

    data = {
        "user_id": session["user_id"],
        "guild_id": int(guild_id),
        "appeal_id": uid,
        "user_name": session["username"]
    }
    headers = {"Authorization": bot_token}
    URL = 'http://127.0.0.1:5000/notify_ban_appeal'
    
    try:
        requests.post(URL, headers=headers, json=data)
        flash("Ban appeal submitted successfully.")
    except requests.RequestException:
        flash("Failed to notify staff about your ban appeal.", "error")
    return redirect(url_for("dashboard"))
        
@app.route('/banappeal/logs/<guild_id>', methods=["GET"])
@login_required
def ban_appeal_logs(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))
    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    management_roles = sett.get("basic_settings", {}).get("management_roles", [])
    if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles):
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    ban_appeals = list(mongo_db["ban_appeals"].find({"guild_id": int(guild_id)}))
    return render_template("ban_appeal_logs.html", guild=guild, ban_appeals=ban_appeals)

@app.route('/banappeal/logs/<guild_id>/<appeal_id>', methods=["GET", "POST"])
@login_required
def ban_appeal_log(guild_id, appeal_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))
    
    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    management_roles = sett.get("basic_settings", {}).get("management_roles", [])
    if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles):
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == "GET":
        appeal = mongo_db["ban_appeals"].find_one({"appeal_id": appeal_id})
        if not appeal:
            flash("Ban appeal not found.", "error")
            return redirect(url_for("ban_appeal_logs", guild_id=guild_id))
        return render_template("ban_appeal_log.html", guild=guild, appeal=appeal)
    
    appeal_document = mongo_db["ban_appeals"].find_one({"appeal_id": appeal_id})
    if not appeal_document:
        flash("Ban appeal not found.", "error")
        return redirect(url_for("ban_appeal_logs", guild_id=guild_id))

    new_status = request.form.get("status")
    mongo_db["ban_appeals"].update_one(
        {"appeal_id": appeal_id},
        {"$set": {"status": new_status}}
    )
    data = {
        "user_id": appeal_document["user_id"],
        "guild_id": int(guild_id),
        "appeal_id": appeal_id,
        "status": new_status,
    }
    headers = {"Authorization": bot_token}
    URL = 'http://127.0.0.1:5000/notify_ban_appeal_status'
    response = requests.post(URL, headers=headers, json=data)
    if response.status_code == 200:
        if new_status == "accepted":
            flash("Ban appeal approved successfully.")
        elif new_status == "denied":
            flash("Ban appeal denied successfully.")
        return redirect(url_for("ban_appeal_logs", guild_id=guild_id))
    else:
        flash("Failed to notify user")
        return redirect(url_for("ban_appeal_logs", guild_id=guild_id))
    
@app.route('/notifications/<guild_id>/<user_id>', methods=["GET"])
@login_required
def notifications(guild_id, user_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Guild not found."}), 404
    
    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}

    if str(user_id) != str(session["user_id"]):
        return jsonify({
            "title": "Unauthorized",
            "message": "You are not authorized to view notifications for this user.",
            "created_at": datetime.now().timestamp(),
            "from": "System"
        }), 403
    

    user_notifications = list(mongo_db["notifications"].find({
        "user_id": str(user_id)
    }))

    notification_list = []
    for notification in user_notifications:
        notification_list.append({
            "title": "Notification",
            "message": notification["message"],
            "created_at": notification["created_at"],
            "from": notification.get("from", "System")
        })

    management_roles = sett.get("basic_settings", {}).get("management_roles", [])
    if any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles):
        erm_api_key = sett.get("erm_api_key", None)
        if erm_api_key:
            all_shifts = get_all_shifts(erm_api_key, guild_id)
            ongoing_shifts = ongoing_shifts_over_4_hours(all_shifts)
            
            if ongoing_shifts:
                for user in ongoing_shifts:
                    notification_list.append({
                        "title": "Shift Grinding Alert",
                        "message": f"{user['nickname']} is having a shift longer than 4 hours.",
                        "created_at": datetime.now().timestamp(),
                        "from": "ERM"
                    })
    return jsonify(notification_list)
    
@app.route('/erm/<guild_id>', methods=["GET"])
@login_required
def erm(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))
    
    member = guild.get_member(int(session["user_id"]))
    if not member:
        flash("You are not a member of this guild.", "error")
        return redirect(url_for("dashboard"))
    
    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    management_roles = sett.get("basic_settings", {}).get("management_roles", [])
    if not any(role in [role.id for role in member.roles] for role in management_roles):
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("erm.html", guild=guild)

@app.route('/erm/authenticate/<guild_id>', methods=["GET", "POST"])
@login_required
def erm_authenticate(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))
    
    member = guild.get_member(int(session["user_id"]))
    if not member:
        flash("You are not a member of this guild.", "error")
        return redirect(url_for("dashboard"))
    
    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    management_roles = sett.get("basic_settings", {}).get("management_roles", [])
    if not any(role in [role.id for role in member.roles] for role in management_roles):
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == "GET":
        return render_template("erm_authenticate.html", guild=guild)
    
    if request.method == "POST":
            api_key = request.form.get("api_key")
            url = "https://core.ermbot.xyz/api/v1/moderations"
            headers = {
                "Authorization": str(api_key),
                "Guild": guild_id
            }
            response = requests.request("GET", url, headers=headers)
            #print(response.json())

            if response.status_code == 200:
                flash("Authentication successful.")
                mongo_db["settings"].update_one(
                    {"_id": guild.id},
                    {"$set": {"erm_api_key": api_key}},
                    upsert=True
                )
            else:
                flash("Authentication failed.", "error")
            return redirect(url_for("dashboard", guild_id=guild_id))
    
@app.route('/erm/shifts/<guild_id>', methods=["GET"])
@login_required
def erm_shifts(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))
    
    member = guild.get_member(int(session["user_id"]))
    if not member:
        flash("You are not a member of this guild.", "error")
        return redirect(url_for("dashboard"))
    
    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    management_roles = sett.get("basic_settings", {}).get("management_roles", [])
    if not any(role in [role.id for role in member.roles] for role in management_roles):
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    
    erm_api_key = sett.get("erm_api_key", None)
    if not erm_api_key:
        flash("Please authenticate with ERM first.", "error")
        return redirect(url_for("erm_authenticate", guild_id=guild_id))
    
    all_shifts = get_all_shifts(erm_api_key, guild_id)
    data = {}
    for shift in all_shifts['data']:
        username = shift['username']
        if username not in data:
            user_id = shift['user_id']
            data[username] = {
                'username': username,
                'nickname': shift['nickname'],
                'user_id': user_id,
                'total_shift_time': total_shift_time(username, all_shifts),
                'alert': ongoing_shift_more_than4h(username, all_shifts),
                'thumbnail': get_roblox_thumbnail(user_id)
            }
    return render_template("erm_shifts.html", guild=guild, data=data)

@app.route('/erm/shifts/<guild_id>/<username>', methods=["GET"])
@login_required
def erm_user_shifts(guild_id, username):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")

    member = guild.get_member(int(session["user_id"]))
    if not member:
        flash("You are not a member of this guild.", "error")
        return redirect(url_for("dashboard"))
    
    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    management_roles = sett.get("basic_settings", {}).get("management_roles", [])
    if not any(role in [role.id for role in member.roles] for role in management_roles):
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    
    erm_api_key = sett.get("erm_api_key", None)
    if not erm_api_key:
        flash("Please authenticate with ERM first.", "error")
        return redirect(url_for("erm_authenticate", guild_id=guild_id))
    
    user_shifts = get_user_shifts(username, guild_id, erm_api_key)
    data = format_shift_data(user_shifts)
    return render_template("erm_user_shifts.html", guild=guild, data=data)


@app.route('/modpanel/<guild_id>', methods=["GET"])
@login_required
def mod_panel(guild_id):
    sett = mongo_db["settings"].find_one({"_id": int(guild_id)}) or {}
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))
    
    member = guild.get_member(int(session["user_id"]))
    if not member:
        flash("You are not a member of this guild.", "error")
        return redirect(url_for("dashboard"))
    
    staff_roles = sett.get("basic_settings", {}).get("staff_roles", [])
    if not any(role in [role.id for role in member.roles] for role in staff_roles):
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))

    return render_template("mod_panel.html", guild=guild, users=guild.members)

@app.route('/modpanel/<guild_id>/modlogs', methods=["GET", "POST"])
@login_required
def mod_logs(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))

    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    staff_roles = sett.get("basic_settings", {}).get("staff_roles", [])
    member = guild.get_member(int(session["user_id"]))
    if not member:
        flash("You are not a member of this guild.", "error")
        return redirect(url_for("dashboard"))

    if not any(role in [role.id for role in member.roles] for role in staff_roles):
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))

    # Pagination logic
    page = int(request.args.get("page", 1))  # Default to page 1
    per_page = 10  # Logs per page
    logs_cursor = list(mongo_db["warnings"].find({"guild_id": int(guild_id)}))
    total_logs = len(logs_cursor)
    total_pages = (total_logs + per_page - 1) // per_page
    logs = logs_cursor[(page - 1) * per_page: page * per_page]

    if request.method == "POST":
        data = request.json
        log_id = data.get("log_id")
        reason = data.get("reason")
        status = data.get("status")

        if not log_id or not reason or status not in ["active", "void"]:
            print("Invalid data received.")
            return jsonify({"success": False, "error": "Invalid data received."})

        try:
            object_id = ObjectId(log_id)  # Ensure ObjectId conversion
        except Exception as e:
            print(e)
            return jsonify({"success": False, "error": "Invalid log ID."})

        log = mongo_db["warnings"].find_one({"_id": object_id, "guild_id": int(guild_id)})
        
        if not log:
            print("Log not found.")
            return jsonify({"success": False, "error": "Log not found."})

        update_result = mongo_db["warnings"].update_one(
            {"_id": object_id},
            {"$set": {"reason": reason, "active": status == "active"}}
        )

        if update_result.modified_count == 0:
            print("No changes made.")
            return jsonify({"success": False, "error": "No changes made."})

        return jsonify({"success": True})

    return render_template(
        "mod_logs.html",
        guild=guild,
        logs=logs,
        total_pages=total_pages,
        current_page=page,
    )

@app.route('/modpanel/<guild_id>/members', methods=["GET", "POST"])
@login_required
def view_members(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))

    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    staff_roles = sett.get("basic_settings", {}).get("staff_roles", [])
    
    member = guild.get_member(int(session["user_id"]))
    if not member:
        flash("You are not a member of this guild.", "error")
        return redirect(url_for("dashboard"))

    if not any(role in [role.id for role in member.roles] for role in staff_roles):
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))

    members = guild.members

    # Apply filtering if POST request
    if request.method == "POST":
        search_query = request.form.get("search_query", "")
        access_filter = request.form.get("access_filter", "all")

        # Filter by username or user ID
        if search_query:
            members = [m for m in members if search_query.lower() in m.name.lower() or search_query in str(m.id)]

        # Filter by role
        if access_filter != "all":
            members = [m for m in members if any(role.name.lower() == access_filter.lower() for role in m.roles)]

    # Pagination - 10 members per page
    page = request.args.get('page', 1, type=int)
    members_per_page = 12
    members_paginated = members[(page - 1) * members_per_page:page * members_per_page]

    return render_template("view_members.html", guild=guild, members=members_paginated, total_pages=(len(members) // members_per_page) + 1, current_page=page)

@app.route('/view_profile/<guild_id>/<user_id>', methods=["GET"])
@login_required
def view_profile(guild_id, user_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))
    
    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    staff_roles = sett.get("basic_settings", {}).get("staff_roles", [])

    member = guild.get_member(int(user_id))
    if not member:
        flash("User not found in this guild.", "error")
        return redirect(url_for("view_members", guild_id=guild_id))
    
    if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in staff_roles):
        flash("You do not have the required permissions to view this profile.", "error")
        return redirect(url_for("view_members", guild_id=guild_id))

    member_roles = [role.name for role in member.roles]
    join_date = member.joined_at.strftime('%Y-%m-%d')

    return render_template("view_profile.html", guild=guild, member=member, roles=member_roles, join_date=join_date)

@app.errorhandler(404)
def page_not_found(e):
    flash("Page not found.", "error")
    return redirect(url_for("index"))

@app.errorhandler(500)
def internal_server_error(e):
    flash("Internal server error.", "error")
    return redirect(url_for("index"))

def run_production():
    serve(app, host='0.0.0.0', port=80)

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=80)