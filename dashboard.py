from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from flask_session import Session
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import requests
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import datetime
import uuid
from waitress import serve
from bson import ObjectId, Int64
from cyni import bot
import markdown
import json

from DashboardModules.WelcomeModule import welcome_route
from DashboardModules.AutoModModule import automod
from DashboardModules.TicketModule import ticket_module
from DashboardModules.loaModule import loa_route

from utils.site_utils import *

FILES_URL = "https://cyni-file-host.x6xkh0.easypanel.host/upload"

load_dotenv()

users = {}

api_token = os.getenv("API_TOKEN", "default_api_token")

FILE_AUTH_TOKEN = os.getenv("FILE_AUTH_TOKEN")

DISCORD_API_BASE_URL = "https://discord.com/api"
OAUTH_SCOPE = "identify guilds"
MANAGE_MESSAGES_PERMISSION = 0x2000
ADMINISTRATOR_PERMISSION = 0x8

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

mongo_client = MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client["cyni"] if os.getenv("PRODUCTION_TOKEN") or os.getenv("PREMIUM_TOKEN") else mongo_client["dev"]
sessions_collection = mongo_db["sessions"]

app.register_blueprint(welcome_route)
app.register_blueprint(automod)
app.register_blueprint(ticket_module)
app.register_blueprint(loa_route)

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Successfully logged in!"

app.config["SESSION_TYPE"] = "mongodb"
app.config["SESSION_MONGODB"] =  mongo_client
app.config["SESSION_MONGODB_DB"] =  "cyni" if os.getenv("PRODUCTION_TOKEN") or os.getenv("PREMIUM_TOKEN") else "dev"
app.config["SESSION_MONGODB_COLLECT"] = "sessions"
Session(app)

bot_token = os.getenv("PRODUCTION_TOKEN") or os.getenv("PREMIUM_TOKEN") or os.getenv("DEV_TOKEN")

class User(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_id(self):
        return self.id

@app.before_request
def ensure_logged_in_user():
    if "user_id" in session and not current_user.is_authenticated:
        user_id = session["user_id"]
        user = load_user(user_id)
        if user:
            login_user(user)

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return users[user_id]
    
    user_session = mongo_db["sessions"].find_one({"user_id": user_id})
    if user_session:
        user_obj = User(user_id)
        users[user_id] = user_obj
        return user_obj

    return None

@app.template_filter('datetime')
def format_datetime(timestamp):
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

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

    sid = request.cookies.get(app.config['SESSION_COOKIE_NAME'])

    mongo_db["sessions"].update_one(
        {"user_id": session["user_id"]},
        {
            "$set": {
                "access_token": access_token,
                "refresh_token": session["refresh_token"],
                "sid": sid
            }
        },
        upsert=True
    )

    next_url = session.pop('next', '/dashboard')
    return redirect(next_url)

@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    session.clear()
    users.pop(user_id, None)
    logout_user()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session or "access_token" not in session:
        sid = request.cookies.get(app.session_cookie_name)
        user_session = None

        if "user_id" in session:
            user_session = mongo_db["sessions"].find_one({"user_id": session["user_id"]})
        elif sid:
            user_session = mongo_db["sessions"].find_one({"sid": sid})

        if user_session:
            session["user_id"] = user_session["user_id"]
            session["access_token"] = user_session["access_token"]
            session["refresh_token"] = user_session.get("refresh_token")
            if user_session["user_id"] not in users:
                users[user_session["user_id"]] = User(user_session["user_id"])
            login_user(users[user_session["user_id"]])
        else:
            return redirect(url_for("login"))

    user_id = session["user_id"]
    username = session.get("username", "")
    access_token = session["access_token"]

    if not username:
        user_response = requests.get(f"{DISCORD_API_BASE_URL}/users/@me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        if user_response.status_code == 200:
            user_json = user_response.json()
            session["username"] = user_json["username"]
            username = user_json["username"]

    guilds_response = requests.get(f"{DISCORD_API_BASE_URL}/users/@me/guilds", headers={
        "Authorization": f"Bearer {access_token}"
    })

    if guilds_response.status_code == 401 and "refresh_token" in session:
        refresh_response = requests.post(f"{DISCORD_API_BASE_URL}/oauth2/token", data={
            "client_id": os.getenv("DISCORD_CLIENT_ID"),
            "client_secret": os.getenv("DISCORD_CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": session["refresh_token"],
            "redirect_uri": os.getenv("DISCORD_REDIRECT_URI"),
            "scope": OAUTH_SCOPE
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if refresh_response.status_code == 200:
            token_json = refresh_response.json()
            session["access_token"] = token_json["access_token"]
            session["refresh_token"] = token_json.get("refresh_token", session["refresh_token"])
            access_token = session["access_token"]
            # Save to DB
            mongo_db["sessions"].update_one(
                {"user_id": session["user_id"]},
                {"$set": {"access_token": access_token, "refresh_token": session["refresh_token"]}},
                upsert=True
            )
            guilds_response = requests.get(f"{DISCORD_API_BASE_URL}/users/@me/guilds", headers={
                "Authorization": f"Bearer {access_token}"
            })
        else:
            return redirect(url_for("login"))

    if guilds_response.status_code != 200:
        return f"Failed to fetch guilds: {guilds_response.text}", 500

    guilds_json = guilds_response.json()

    if not isinstance(guilds_json, list):
        return f"Unexpected response format: {guilds_json}", 500

    whitelabel_bots = {}
    main_bot_guilds = []
    user_guilds = []
    
    all_bot_guilds = {
        CYNI_API_BASE_URL: set(get_bot_guilds(CYNI_API_BASE_URL)),
        CYNI_PREMIUM_URL: set(get_bot_guilds(CYNI_PREMIUM_URL)),
    }
    all_bot_guilds.update({api_url: set(get_bot_guilds(api_url)) for api_url in whitelabel_bots})
    
    combined_bot_guild_ids = set().union(*all_bot_guilds.values())
    
    seen_guild_ids = set()
    
    for guild in guilds_json:
        gid = guild["id"]
        if gid in seen_guild_ids:
            continue
        for api_url, guild_ids in whitelabel_bots.items():
            if gid in all_bot_guilds[api_url] and gid in guild_ids:
                guild["api_url"] = api_url
                user_guilds.append(guild)
                seen_guild_ids.add(gid)
                break
        else:
            if gid in all_bot_guilds[CYNI_API_BASE_URL] and gid in main_bot_guilds:
                guild["api_url"] = CYNI_API_BASE_URL
                user_guilds.append(guild)
                seen_guild_ids.add(gid)
            elif gid in all_bot_guilds[CYNI_PREMIUM_URL]:
                guild["api_url"] = CYNI_PREMIUM_URL
                user_guilds.append(guild)
                seen_guild_ids.add(gid)

    official_guild_id = '1152949579407442050'
    affiliated_guild_ids = [guild['guild_id'] for guild in list(mongo_db["affiliated_guilds"].find())]

    for guild in guilds_json:
        permissions = guild.get("permissions", 0)
        has_manage_messages = (permissions & MANAGE_MESSAGES_PERMISSION) == MANAGE_MESSAGES_PERMISSION
        is_admin = (permissions & ADMINISTRATOR_PERMISSION) == ADMINISTRATOR_PERMISSION
        is_owner = guild.get("owner", False)
        bot_present = guild["id"] in combined_bot_guild_ids
        premium_status = False
        try:
            p_check = mongo_db["premium"].find_one({"_id": int(guild["id"])})
            premium_status = p_check is not None
        except Exception as e:
            pass

        if (has_manage_messages or is_admin or is_owner) and bot_present:
            user_guilds.append({
                "id": guild["id"],
                "name": guild["name"],
                "icon": guild["icon"],
                "owner": is_owner,
                "official": True if guild["id"] == official_guild_id else False,
                "affiliated": True if int(guild["id"]) in affiliated_guild_ids else False,
                "admin": is_admin,
                "moderator": has_manage_messages,
                "premium": premium_status,
                "member_count": guild.get("member_count", 0),
            })

    session["guilds"] = user_guilds
    return render_template("dashboard.html", user_id=user_id, username=username, user_guilds=user_guilds)

@app.route('/dashboard/<guild_id>', methods=["GET", "POST"])
@login_required
def guild(guild_id):

    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))

    settings = mongo_db["settings"].find_one({"_id": int(guild_id)})
    app_count = mongo_db["applications"].count_documents({"guild_id": guild_id})

    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))

    if guild and isinstance(guild.get("created_at", None), str):
        try:
            guild["created_at"] = datetime.datetime.fromisoformat(guild["created_at"])
        except Exception:
            pass
    return render_template("guild.html", guild=guild, guild_data=settings, app_count=app_count)

@app.route('/dashboard/<guild_id>/settings/basics', methods=["GET", "POST"])
@login_required
def guild_settings_basics(guild_id):

    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))

    guild_data = mongo_db["settings"].find_one({"_id": int(guild_id)}) or {}

    customization = guild_data.get("customization", {})
    prefix = customization.get("prefix", "?")
    premium_prefix = customization.get("premium_prefix", "?")
    basic_settings = guild_data.get("basic_settings", {})
    staff_roles = basic_settings.get("staff_roles", [])
    management_roles = basic_settings.get("management_roles", [])

    roles = get_guild_roles(guild_id)
    if not roles:
        flash("There was an error fetching roles for this guild.", "error")
        return redirect(url_for("guild", guild_id=guild_id))

    if request.method == "POST":
        prefix = request.form.get("prefix")
        staff_roles = request.form.getlist("staff_roles")
        management_roles = request.form.getlist("management_roles")
        premium_prefix = request.form.get("premium_prefix", "?")

        staff_roles = [int(role) for role in staff_roles]
        management_roles = [int(role) for role in management_roles]
        
        try:
            mongo_db["settings"].update_one(
                {"_id": int(guild_id)},
                {
                    "$set": {
                        "customization.prefix": prefix,
                        "customization.premium_prefix": premium_prefix,
                        "basic_settings.staff_roles": staff_roles,
                        "basic_settings.management_roles": management_roles
                    }
                },
                upsert=True
            )
            flash("Settings updated successfully!", "success")
        except Exception as e:
            flash(f"Error updating settings: {e}", "error")
        return redirect(url_for("guild_settings_basics", guild_id=guild_id))
    
    premium_status = False
    sett = mongo_db["premium"].find_one({"_id": Int64(guild_id)})
    if sett: premium_status = True
    return render_template("guild_settings_basics.html", guild=guild, guild_data=guild_data, roles=roles, premium_status=premium_status)

@app.route('/dashboard/<guild_id>/settings/anti-ping', methods=["GET", "POST"])
@login_required
def anti_ping_settings(guild_id):

    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    
    guild_data = mongo_db["settings"].find_one({"_id": int(guild_id)}) or {}

    anti_ping_module = guild_data.get("anti_ping_module", {})
    affected_roles = anti_ping_module.get("affected_roles", [])
    exempt_roles = anti_ping_module.get("exempt_roles", [])
    enabled = anti_ping_module.get("enabled", False)
    
    roles = get_guild_roles(guild_id)
    if not roles:
        flash("No roles found in this guild.", "error")
        return redirect(url_for("guild", guild_id=guild_id))

    if request.method == "POST":
        affected_roles = request.form.getlist("affected_roles")
        exempt_roles = request.form.getlist("exempt_roles")
        enabled = request.form.get("enabled") == "on" 

        affected_roles = [int(role) for role in affected_roles]
        exempt_roles = [int(role) for role in exempt_roles]

        mongo_db["settings"].update_one(
            {"_id": int(guild_id)},
            {
                "$set": {
                    "anti_ping_module.affected_roles": affected_roles,
                    "anti_ping_module.exempt_roles": exempt_roles,
                    "anti_ping_module.enabled": enabled
                }
            },
            upsert=True
        )
        return redirect(url_for("anti_ping_settings", guild_id=guild_id))

    return render_template("anti_ping_settings.html", guild=guild, guild_data=guild_data, roles=roles)

@app.route('/dashboard/<guild_id>/settings/moderation', methods=["GET", "POST"])
@login_required
def moderation_settings(guild_id):
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    
    guild_data = mongo_db["settings"].find_one({"_id": int(guild_id)}) or {}

    moderation_module = guild_data.get("moderation_module", {})
    enabled = moderation_module.get("enabled", False)
    mod_log_channel = moderation_module.get("mod_log_channel", None)
    ban_appeal_channel = moderation_module.get("ban_appeal_channel", None)
    audit_log_channel = moderation_module.get("audit_log", None)

    channels = get_guild_channels(guild_id)
    if not channels:
        flash("No channels found in this guild.", "error")
        return redirect(url_for("guild", guild_id=guild_id))

    if request.method == "POST":
        enabled = request.form.get("enabled") == "on"
        mod_log_channel = request.form.get("mod_log_channel")
        ban_appeal_channel = request.form.get("ban_appeal_channel")
        audit_log_channel = request.form.get("audit_log_channel")

        mongo_db["settings"].update_one(
            {"_id": int(guild_id)},
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
        return redirect(url_for("moderation_settings", guild_id=guild_id))

    return render_template("moderation_settings.html", guild=guild, guild_data=guild_data, channels=channels)

@app.route('/applications/<guild_id>', methods=["GET"])
@login_required
def applications_dashboard(guild_id):
    try:
        guild = get_guild(guild_id)
        if not guild:
            flash("Guild not found or you do not have access to it.", "error")
            return redirect(url_for("dashboard"))

        member = get_guild_member(guild_id, session["user_id"])
        if not member:
            flash("You do not have access to this guild.", "error")
            return redirect(url_for("dashboard"))
        
        has_perm = check_permissions(guild_id, session["user_id"])
        if has_perm is False:
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("dashboard"))

        return render_template("applications/index.html", guild=guild)
    except Exception as e:
        print(f"Error in applications_dashboard: {e} in /applications/{guild_id}")
        return redirect(url_for("dashboard"))

@app.route('/applications/manage/<guild_id>', methods=["GET"])
@login_required
def applications(guild_id):
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))

    all_applications = list(mongo_db["applications"].find({"guild_id": int(guild_id)}))
    return render_template("applications/applications.html", applications=all_applications, guild=guild)

@app.route('/applications/manage/<guild_id>/create', methods=["POST","GET"])
@login_required
def create_application(guild_id):
    if request.method == "GET":
        guild = get_guild(guild_id)
        if not guild:
            flash("Guild not found or you do not have access to it.", "error")
            return redirect(url_for("dashboard"))

        member = get_guild_member(guild_id, session["user_id"])
        if not member:
            flash("You do not have access to this guild.", "error")
            return redirect(url_for("dashboard"))
        
        has_perm = check_permissions(guild_id, session["user_id"])
        if has_perm is False:
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("dashboard"))
        return render_template("applications/create_application.html", guild=guild)

    elif request.method == "POST":
        if current_user.is_authenticated:
            guild = get_guild(guild_id)
            if not guild:
                flash("Guild not found or you do not have access to it.", "error")
                return redirect(url_for("dashboard"))

            member = get_guild_member(guild_id, session["user_id"])
            if not member:
                flash("You do not have access to this guild.", "error")
                return redirect(url_for("dashboard"))
            
            has_perm = check_permissions(guild_id, session["user_id"])
            if has_perm is False:
                flash("You do not have the required permissions to access this page.", "error")
                return redirect(url_for("dashboard"))
            
            application_name = request.form.get("application_name")
            application_description = request.form.get("application_description")
            required_roles = request.form.get("required_roles", "")
            required_roles = [int(role.strip()) for role in required_roles.split(',') if role.strip()] if required_roles else []
            application_channel = int(request.form.get("application_channel"))
            all_questions = request.form.getlist("question")
            pass_role = int(request.form.get("pass_role"))
            fail_role = int(request.form.get("fail_role"))
            theme_color = request.form.get("theme_color", "amber")

            form_structure = request.form.get("form_structure")
            
            final_questions = []
            if form_structure and form_structure.strip():
                try:
                    form_data = json.loads(form_structure)
                    
                    for section in form_data.get("sections", []):
                        for question in section.get("questions", []):
                            final_questions.append({"question": question.get("text", "")})
                    
                except Exception as e:
                    final_questions = [{"question": question} for question in all_questions]
            else:
                final_questions = [{"question": question} for question in all_questions]
            if not final_questions:
                flash("Error: No questions found in the application form. Please add at least one question.", "error")
                return redirect(url_for("create_application", guild_id=guild_id))
            
            application_data = {
                "guild_id": int(guild_id),
                "name": application_name,
                "description": application_description,
                "required_roles": required_roles,
                "questions": final_questions,
                "application_channel": application_channel,
                "pass_role": pass_role,
                "fail_role": fail_role,
                "status": "open",
                "theme_color": theme_color,
                "created_at": datetime.datetime.now().timestamp(),
            }
            
            if form_structure:
                try:
                    form_data = json.loads(form_structure)
                    application_data["form_structure"] = form_data
                except:
                    pass
            
            mongo_db["applications"].insert_one(application_data)
            
            saved_application = mongo_db["applications"].find_one({"_id": application_data.get("_id")})
            if not saved_application:
                saved_application = mongo_db["applications"].find_one({
                    "guild_id": int(guild_id),
                    "name": application_name
                }, sort=[("created_at", -1)])

            flash("Application created successfully!", "success")
            return redirect(url_for("applications", guild_id=guild_id))

@app.route('/applications/manage/<guild_id>/<application_id>', methods=["GET", "POST"])
@login_required
def manage_application(guild_id, application_id):
    application = mongo_db["applications"].find_one({"_id": ObjectId(application_id)})
    if request.method == "GET":
        guild = get_guild(guild_id)
        if not guild:
            flash("Guild not found or you do not have access to it.", "error")
            return redirect(url_for("dashboard"))

        member = get_guild_member(guild_id, session["user_id"])
        if not member:
            flash("You do not have access to this guild.", "error")
            return redirect(url_for("dashboard"))
        
        has_perm = check_permissions(guild_id, session["user_id"])
        if has_perm is False:
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("dashboard"))
        if not application:
            return redirect(url_for("applications", guild_id=guild_id))
        return render_template("applications/manage_application.html", guild=guild, application=application)

    if request.method == "POST":
        application_name = request.form.get("application_name")
        application_description = request.form.get("application_description")
        required_roles = request.form.get("required_roles", "")
        required_roles = [int(role.strip()) for role in required_roles.split(',') if role.strip()] if required_roles else []
        application_channel = int(request.form.get("application_channel"))
        all_questions = request.form.getlist("question")
        pass_role = int(request.form.get("pass_role"))
        fail_role = int(request.form.get("fail_role"))
        status = request.form.get("status")
        theme_color = request.form.get("theme_color", application.get("theme_color", "amber"))
        banner_file = request.files.get("banner_image")
        remove_banner = request.form.get("remove_banner") == "true"

        banner_image_url = None
        if remove_banner:
            banner_image_url = ""
        elif banner_file and banner_file.filename != "":
            try:
                if not banner_file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    flash("Invalid file type. Please upload a PNG, JPG, JPEG, or GIF image.", "error")
                    return redirect(url_for("manage_application", guild_id=guild_id, application_id=application_id))
                files_response = requests.post(
                    FILES_URL,
                    files={"file": (banner_file.filename, banner_file, banner_file.content_type)},
                )
                if files_response.status_code == 200:
                    banner_image_url = files_response.json().get("url")
                else:
                    flash("Error uploading banner image.", "error")
            except Exception as e:
                flash(f"Error uploading banner: {e}", "error")
            try:
                pass
            except Exception as e:
                flash(f"Error processing banner: {e}", "error")

        form_structure = request.form.get("form_structure")
        final_questions = []
        
        if form_structure and form_structure.strip():
            try:
                form_data = json.loads(form_structure)
                print(f"DEBUG: Parsed form data: {form_data}")
                
                for section in form_data.get("sections", []):
                    print(f"DEBUG: Processing section: {section}")
                    for question in section.get("questions", []):
                        print(f"DEBUG: Processing question: {question}")
                        final_questions.append({"question": question.get("text", "")})
                        
            except Exception as e:
                print(f"Error parsing form structure in manage_application: {e}")
                final_questions = [{"question": question} for question in all_questions]
        else:
            if application and "form_structure" in application and application["form_structure"]:
                print("DEBUG: Using existing form_structure from database")
                try:
                    form_data = application["form_structure"]
                    print(f"DEBUG: Existing form data: {form_data}")
                    
                    for section in form_data.get("sections", []):
                        print(f"DEBUG: Processing existing section: {section}")
                        for question in section.get("questions", []):
                            print(f"DEBUG: Processing existing question: {question}")
                            final_questions.append({"question": question.get("text", "")})
                            
                except Exception as e:
                    final_questions = [{"question": question} for question in all_questions]
            else:
                final_questions = [{"question": question} for question in all_questions]
        
        if not final_questions:
            flash("Error: No questions found in the application form. Please add at least one question.", "error")
            return redirect(url_for("manage_application", guild_id=guild_id, application_id=application_id))

        application_data = {
            "guild_id": int(guild_id),
            "name": application_name,
            "description": application_description,
            "required_roles": required_roles,
            "questions": final_questions,
            "application_channel": application_channel,
            "pass_role": pass_role,
            "fail_role": fail_role,
            "status": status,
            "theme_color": theme_color
        }
        
        if banner_image_url is not None:
            application_data["banner_image"] = banner_image_url
        
        form_structure = request.form.get("form_structure")
        if form_structure:
            try:
                form_data = json.loads(form_structure)
                application_data["form_structure"] = form_data
            except:
                pass
        elif "form_structure" in application:
            application_data["form_structure"] = application["form_structure"]

        mongo_db["applications"].update_one(
            {"_id": ObjectId(application_id)},
            {"$set": application_data}
        )
        flash("Application updated successfully!", "success")
        return redirect(url_for("applications", guild_id=guild_id))

@app.route('/applications/apply/<guild_id>/<application_id>', methods=["GET", "POST"])
@login_required
def apply(guild_id, application_id):
    if request.method == "GET":
        guild = get_guild(guild_id)
        if not guild:
            flash("Guild not found or you do not have access to it.", "error")
            return redirect(url_for("dashboard"))

        member = get_guild_member(guild_id, session["user_id"])
        if not member:
            flash("You do not have access to this guild.", "error")
            return redirect(url_for("dashboard"))
        
        has_perm = check_permissions(guild_id, session["user_id"])
        if has_perm is False:
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("dashboard"))
        
        try:
            application = mongo_db["applications"].find_one({"_id": ObjectId(application_id)})
        except Exception as e:
            flash(f"Invalid application ID: {e}", "error")
            return redirect(url_for("dashboard"))
        
        if not application:
            flash("Application not found.", "error")
            return redirect(url_for("dashboard"))
        
        if application.get("status") == "close":
            flash("This application is currently closed.", "error")
            return redirect(url_for("dashboard"))

        existing_application = mongo_db["user_applications"].find_one({
            "user_id": session["user_id"],
            "application_id": str(application_id),
            "status": "pending"
        })
        if existing_application:
            flash("You have already submitted an application that is pending review.", "error")
            return redirect(url_for("dashboard"))
        
        markdown_application_description = application.get("description", "")
        application['description'] = markdown.markdown(markdown_application_description, extensions=['extra', 'codehilite', 'smarty'])
        
        return render_template("applications/apply.html", guild=guild, application=application)

    if request.method == "POST":
        try:
            if ObjectId.is_valid(application_id):
                application = mongo_db["applications"].find_one({"_id": ObjectId(application_id)})
            else:
                flash("Invalid application ID.", "error")
                return redirect(url_for("dashboard"))
                
            if not application:
                flash("Application not found.", "error")
                return redirect(url_for("dashboard"))
            
            has_perm = check_permissions(guild_id, session["user_id"])
            if has_perm is False:
                flash("You do not have the required permissions to access this page.", "error")
                return redirect(url_for("dashboard"))
            
            existing_application = mongo_db["user_applications"].find_one({
                "user_id": session["user_id"],
                "application_id": str(application_id),
                "status": "pending"
            })
            if existing_application:
                flash("You have already submitted an application that is pending review.", "error")
                return redirect(url_for("dashboard"))
            
            answers = []
            
            if "form_structure" in application:
                question_count = 0
                for section in application["form_structure"].get("sections", []):
                    for question in section.get("questions", []):
                        question_count += 1
                        answer_key = f"answer_{question_count}"
                        answer = request.form.get(answer_key, "")
                        
                        answers.append({
                            "question": question.get("text", "Question"),
                            "answer": answer,
                            "type": question.get("type", "text")
                        })
            else:
                answers = [
                    {"question": q["question"], "answer": request.form.get(f"answer_{i+1}", ""), "type": "text"}
                    for i, q in enumerate(application["questions"])
                ]
            
            application_data = {
                "guild_id": int(guild_id),
                "name": str(member.name),
                "user_id": str(member.id),
                "application_id": str(application_id),
                "application_name": application["name"],
                "answers": answers,
                "status": "pending",
                "created_at": datetime.datetime.now().timestamp()
            }
            
            data = {
                "guild_id": int(guild_id),
                "user_id": str(member.id),
                "application_name": application["name"],
                "application_channel": application["application_channel"],
                "application_id": str(application_id),
                "result_channel_id": application.get("application_channel"),
            }
            headers = {"Authorization": api_token}
            URL = 'http://127.0.0.1:5000/notify_application_submission'
            try:
                response = requests.post(URL, headers=headers, json=data, timeout=10)
                response.raise_for_status()  # This will raise an exception for bad status codes
            except requests.exceptions.RequestException as e:
                print(f"Failed to send notification: {e}")
                
            mongo_db["user_applications"].insert_one(application_data)
            flash("Application submitted successfully!", "success")
            return redirect(url_for("dashboard"))
            
        except Exception as e:
            flash("An error occurred while submitting your application.", "error")
            return redirect(url_for("dashboard"))
    
@app.route('/applications/logs/<guild_id>', methods=["GET"])
@login_required
def application_logs(guild_id):
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))

    user_applications = list(mongo_db["user_applications"].find(
        {"guild_id": int(guild_id)}
    ))

    return render_template("applications/application_logs.html", guild=guild, user_applications=user_applications)

@app.route('/applications/logs/<guild_id>/<application_id>/<user_id>', methods=["GET", "POST"])
@login_required
def user_application(guild_id, application_id, user_id):
    if request.method == "GET":
        guild = get_guild(guild_id)
        if not guild:
            flash("Guild not found or you do not have access to it.", "error")
            return redirect(url_for("dashboard"))

        member = get_guild_member(guild_id, session["user_id"])
        if not member:
            flash("You do not have access to this guild.", "error")
            return redirect(url_for("dashboard"))
        
        has_perm = check_permissions(guild_id, session["user_id"])
        if has_perm is False:
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("dashboard"))

        application = mongo_db["applications"].find_one({"_id": ObjectId(application_id)})
        if not application:
            return redirect(url_for("applications", guild_id=guild_id))

        user_application = mongo_db["user_applications"].find_one({
            "guild_id": Int64(guild_id),
            "user_id": str(user_id),
            "application_id": str(application_id)
        })
        if not user_application:
            return redirect(url_for("application_logs", guild_id=guild_id))
        
        return render_template("applications/user_application.html", guild=guild, application=application, user_application=user_application)

    if request.method == "POST":
        has_perm = check_permissions(guild_id, session["user_id"])
        if has_perm is False:
            flash("You do not have the required permissions to access this page.", "error")
            return redirect(url_for("dashboard"))
            
        application = mongo_db["applications"].find_one({"_id": ObjectId(application_id)})
        if not application:
            return redirect(url_for("applications", guild_id=guild_id))
        
        user_application = mongo_db["user_applications"].find_one({
            "guild_id": Int64(guild_id),
            "user_id": str(user_id),
            "application_id": str(application_id)
        })
        if not user_application:
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
        headers = {"Authorization": api_token}
        URL = 'http://127.0.0.1:5000/notify_user'
        requests.post(URL, headers=headers, json=data)
        return redirect(url_for("application_logs", guild_id=guild_id))

@app.route('/banappeal/manage/<guild_id>', methods=["GET", "POST"])
@login_required
def ban_appeal_manage(guild_id):
    if request.method == "GET":
        guild = get_guild(guild_id)
        if not guild:
            flash("Guild not found or you do not have access to it.", "error")
            return redirect(url_for("dashboard"))

        member = get_guild_member(guild_id, session["user_id"])
        if not member:
            flash("You do not have access to this guild.", "error")
            return redirect(url_for("dashboard"))
        
        has_perm = check_permissions(guild_id, session["user_id"])
        if has_perm is False:
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
        return render_template("banappeal/ban_appeal_manage.html", guild=guild, appeal_application=appeal_application)
    
    if request.method == "POST":
        has_perm = check_permissions(guild_id, session["user_id"])
        if has_perm is False:
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

@app.route('/banappeal/<guild_id>', methods=["GET", "POST"])
@login_required
def ban_appeal(guild_id):
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
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
        
        return render_template("banappeal/ban_appeal.html", guild=guild, appeal_application=appeal_application)
    
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
        "timestamp": datetime.datetime.now(),
        "username": session["username"]
    }
    mongo_db["ban_appeals"].insert_one(appeal_data)

    data = {
        "user_id": session["user_id"],
        "guild_id": int(guild_id),
        "appeal_id": uid,
        "user_name": session["username"]
    }
    headers = {"Authorization": api_token}
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
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    ban_appeals = list(mongo_db["ban_appeals"].find({"guild_id": int(guild_id)}))
    return render_template("banappeal/ban_appeal_logs.html", guild=guild, ban_appeals=ban_appeals)

@app.route('/banappeal/logs/<guild_id>/<appeal_id>', methods=["GET", "POST"])
@login_required
def ban_appeal_log(guild_id, appeal_id):
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == "GET":
        appeal = mongo_db["ban_appeals"].find_one({"appeal_id": appeal_id})
        if not appeal:
            flash("Ban appeal not found.", "error")
            return redirect(url_for("ban_appeal_logs", guild_id=guild_id))
        return render_template("banappeal/ban_appeal_log.html", guild=guild, appeal=appeal)
    
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
    headers = {"Authorization": api_token}
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

@app.route('/panel/discord/<guild_id>', methods=["GET"])
@login_required
def discord_mod_panel(guild_id):
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    
    users = get_guild_members(guild_id)
    if not users:
        flash("No users found in this guild.", "info")

    return render_template("mod_panel.html", guild=guild, users=users)

@app.route('/panel/discord/<guild_id>/modlogs', methods=["GET", "POST"])
@login_required
def discord_mod_logs(guild_id):
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
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

@app.route('/panel/discord/<guild_id>/members', methods=["GET", "POST"])
@login_required
def discord_view_members(guild_id):
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))
    
    members = get_guild_members(guild_id)
    if not members:
        flash("No members found in this guild.", "info")
        return render_template("view_members.html", guild=guild, members=[], total_pages=0, current_page=1)

    if request.method == "POST":
        search_query = request.form.get("search_query", "")
        access_filter = request.form.get("access_filter", "all")

        if search_query:
            members = [m for m in members if search_query.lower() in m.name.lower() or search_query in str(m.id)]

        if access_filter != "all":
            members = [m for m in members if any(role.name.lower() == access_filter.lower() for role in m.roles)]

    page = request.args.get('page', 1, type=int)
    members_per_page = 12
    members_list = list(members)
    members_paginated = members_list[(page - 1) * members_per_page:page * members_per_page]

    return render_template("view_members.html", guild=guild, members=members_paginated, total_pages=(len(members_list) // members_per_page) + 1, current_page=page)

@app.route('/panel/discord/<guild_id>/<user_id>', methods=["GET"])
@login_required
def discord_view_profile(guild_id, user_id):
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(guild_id, user_id)
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
        flash("You do not have the required permissions to access this page.", "error")
        return redirect(url_for("dashboard"))

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

@app.route('/api/v1/vote', methods=['POST'])
def vote_tracker_api():
    AUTH_TOKEN = 'Hfup2GkgPzgmcjzrmpE2JP37fNFMCUB7Tg3d4Wm'
    auth_header = request.headers.get('Authorization')
    if auth_header != AUTH_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    URL = "http://127.0.0.1:5000/bot_vote_notification"
    try:
        response = requests.post(URL, json=data, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to notify bot of vote: {e}")
        return jsonify({"error": "Failed to notify bot"}), 500
    return jsonify({"status": "success", "message": "Vote recorded"}), 200

@app.route("/docs")
def docs():
    return redirect(url_for("index"))

@app.route("/premium")
def premium():
    return render_template("premium.html")

@app.route('/giveaway/<message_id>', methods=["GET","POST"])
def giveaway(message_id):
    giveaway = mongo_db["giveaways"].find_one({"message_id": int(message_id)})
    if not giveaway:
        return redirect(url_for("dashboard"))

    return render_template("active_giveaway.html", guild=guild, giveaway=giveaway)

def run_production():
    serve(app, host='0.0.0.0', port=80)

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=80, debug=True)