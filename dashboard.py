from flask import Flask, session, render_template, request, redirect, url_for, current_app, flash
from flask_session import Session
from flask_login import LoginManager, login_required, login_user, logout_user, UserMixin, current_user
import requests
import os
from flask.sessions import SessionInterface
from dotenv import load_dotenv
from waitress import serve
import socket
from pymongo import MongoClient
from bson import ObjectId
from cyni import bot
import datetime
import bson
from cyni import fetch_invite
import discord

load_dotenv()

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
DISCORD_API_BASE_URL = "https://discord.com/api"
OAUTH_SCOPE = "identify guilds"

directory_mode = os.getenv("DIRECTORY_MODE")
if directory_mode == "True":
    directory_mode = True
else:
    directory_mode = False

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

mongo_client = MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client["cyni"]
sessions_collection = mongo_db["sessions"]

class MongoSessionInterface(SessionInterface):
    def __init__(self, session_collection):
        self.session_collection = session_collection

    def open_session(self, app, request):
        session_cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
        session_id = request.cookies.get(session_cookie_name)
        if session_id:
            try:
                session_data = self.session_collection.find_one({"_id": session_id})
                if session_data and session_data.get('logged_in'):
                    return session_data.get('data', {})
            except bson.errors.InvalidId:
                pass
        return {}

    def save_session(self, app, session, response):
        session_cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
        user_id = session.get('user_id')
        
        if not user_id:
            return

        session_id = str(user_id)

        session_data = dict(session)
        session_data['logged_in'] = True

        self.session_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "data": session_data,
                    "logged_in": True,
                    "expiration": datetime.datetime.now() + app.permanent_session_lifetime
                }
            },
            upsert=True
        )

        response.set_cookie(session_cookie_name, session_id, httponly=True, max_age=app.permanent_session_lifetime)

app.session_interface = MongoSessionInterface(sessions_collection)

class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    discord_login_url = (
        f"{DISCORD_API_BASE_URL}/oauth2/authorize?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope={OAUTH_SCOPE}"
    )
    return redirect(discord_login_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Authorization code not found.", 400
    
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "scope": OAUTH_SCOPE
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_response = requests.post(f"{DISCORD_API_BASE_URL}/oauth2/token", data=data, headers=headers)
    
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

    if user_json["id"] not in users:
        users[user_json["id"]] = User(user_json["id"])
        login_user(users[user_json["id"]])

    return redirect(url_for("dashboard"))

MANAGE_MESSAGES_PERMISSION = 0x2000
ADMINISTRATOR_PERMISSION = 0x8

@app.route("/dashboard")
@login_required
def dashboard():
    if "user_id" in session:
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
        #print(user_guilds)
        return render_template("dashboard.html", user_id=user_id, username=username, user_guilds=user_guilds)
    
    return redirect(url_for("login"))

@app.route('/dashboard/guild/<guild_id>', methods=["GET", "POST"])
@login_required
def guild(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        return render_template("404.html"), 404
    member = guild.get_member(int(session["user_id"]))
    if not member:
        return "You are not a member of this guild.", 403
    if not member.guild_permissions.manage_guild or not member.guild_permissions.administrator:
        return "You do not have the required permissions to access this page.", 403
    return render_template("guild.html", guild=guild)

@app.route('/dashboard/guild/<guild_id>/antiping', methods=["GET", "POST"])
@login_required
async def antiping(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        return render_template("404.html"), 404
    member = guild.get_member(int(session["user_id"]))
    if not member:
        return render_template("403.html"), 403
    if not member.guild_permissions.manage_guild or not member.guild_permissions.administrator:
        return render_template("403.html"), 403
    sett = await bot.settings.find_by_id(guild_id)
    if request.method == "POST":
        enabled = request.form.get("enabled") == "True"
        affected_roles = request.form.getlist("affected_roles")
        exempt_roles = request.form.getlist("exempt_roles")
        sett["anti_ping_module"] = {
            "enabled": enabled,
            "affected_roles": affected_roles,
            "exempt_roles": exempt_roles
        }
        await bot.settings.update_by_id(guild_id, sett)
        return redirect(url_for("guild", guild_id=guild_id))
    else:
        affected_roles = sett.get("anti_ping_module", {}).get("affected_roles", [])
        exempt_roles = sett.get("anti_ping_module", {}).get("exempt_roles", [])
        enabled = sett.get("anti_ping_module", {}).get("enabled", False)
        return render_template(
            "antiping.html", 
            guild=guild, 
            affected_roles=affected_roles, 
            exempt_roles=exempt_roles, 
            enabled=enabled
        )

@app.route("/logout")
def logout():
    try:
        user_id = session.get("user_id")
        session.clear()
        users.pop(user_id,None)
        if user_id:
            sessions_collection.update_one(
                {"_id": user_id},
                {"$set": {"logged_in": False}}
            )
        logout_user()
    except KeyError:
        pass
    finally:
        return redirect(url_for("index"))
    
@app.route("/docs")
def docs():
    return render_template("docs.html")

@app.route("/docs/config")
def docs_config():
    return render_template("config.html")

@app.route('/directory')
def directory():
    if not directory_mode:
        return render_template("under_development.html")
    return render_template("directory.html")

import asyncio

def get_invite(guild_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        invite_url = loop.run_until_complete(fetch_invite(guild_id))
        return invite_url
    except Exception as e:
        return str(e)

@app.route('/directory/<guild_id>')
def directory_guild(guild_id):
    if not directory_mode:
        return render_template("under_development.html")
    try:
        guild_id_int = int(guild_id)
    except ValueError:
        return "Invalid guild ID.", 400
    
    invite_url = get_invite(guild_id_int)
    
    if "Failed" in invite_url or "Guild not found" in invite_url:
        return f"Failed to get invite: {invite_url}", 404

    guild = bot.get_guild(guild_id_int)
    if guild is None:
        return "Guild not found.", 404
    
    return render_template("directory_guild.html", guild=guild, invite=invite_url)

@app.route('/directory/<guild_id>/add')
@login_required
def directory_add(guild_id):
    if not directory_mode:
        return render_template("under_development.html")
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        return "Guild not found.", 404
    return render_template("directory_add.html", guild=guild)

@app.route('/directory/<guild_id>/edit')
@login_required
def directory_edit(guild_id):
    if not directory_mode:
        return render_template("under_development.html")
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        return "Guild not found.", 404
    return render_template("directory_edit.html", guild=guild)

@app.route('/directory/<guild_id>/vote')
@login_required
def directory_view(guild_id):
    if not directory_mode:
        return render_template("under_development.html")
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        return "Guild not found.", 404
    return render_template("directory_view.html", guild=guild)

@app.route('/dashboard/guild/<guild_id>/massdemote', methods=["GET", "POST"])
@login_required
def massdemote(guild_id):
    # Convert guild_id to integer if needed
    guild_id = int(guild_id)

    # Get the guild from the Discord bot
    guild = bot.get_guild(guild_id)
    if not guild:
        flash("Guild not found.")
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        # Extracting form data
        members = request.form.getlist("members")
        role_id = request.form.get("role_id")
        punishment = request.form.get("punishment")
        reason = request.form.get("reason")
        rank = request.form.get("rank")

        # Validate form inputs
        if not members or not role_id:
            flash("Please select members and a role.")
            return redirect(url_for("massdemote", guild_id=guild_id))

        # Get the role from the guild
        role = guild.get_role(int(role_id))
        if not role:
            flash("Role not found.")
            return redirect(url_for("massdemote", guild_id=guild_id))

        for member_id in members:
            member = guild.get_member(int(member_id))
            if member:
                try:
                    # Removing the role from the member
                    bot.loop.create_task(member.remove_roles(role))
                except Exception as e:
                    print(f"Error removing role from {member}: {e}")
                    flash(f"Error demoting {member.name}: {e}")
            else:
                flash(f"Member with ID {member_id} not found.")

        # Fetch server settings (using bot.loop.run_until_complete to run async code)
        sett = bot.loop.run_until_complete(bot.settings.find_by_id(guild_id))
        if not sett:
            flash("Settings not found.")
            return redirect(url_for("guild", guild_id=guild_id))

        # Check if the staff management module is enabled
        enabled = sett['staff_management'].get("enabled", False)
        if not enabled:
            flash("Staff management module is not enabled.")
            return redirect(url_for("guild", guild_id=guild_id))

        # Get the demotion channel from settings
        demotion_channel_id = sett["staff_management"].get("demotion_channel")
        if not demotion_channel_id:
            flash("Demotion channel not set.")
            return redirect(url_for("guild", guild_id=guild_id))

        demotion_channel = guild.get_channel(demotion_channel_id)
        if not demotion_channel:
            flash("Demotion channel not found.")
            return redirect(url_for("guild", guild_id=guild_id))

        # Send demotion notifications and log infractions
        for member_id in members:
            count = bot.loop.run_until_complete(bot.infraction_log.count_all({"guild_id": guild.id}))
            member = guild.get_member(int(member_id))
            if member:
                # Creating the embed for the demotion
                infract_embed = discord.Embed(
                    title=f"{member} has been demoted.",
                    description=" ",
                )
                if reason:
                    infract_embed.add_field(name="Reason", value=reason)
                if punishment:
                    infract_embed.add_field(name="Punishment", value=punishment)
                infract_embed.set_footer(text=f"Case {count + 1}")
                infract_embed.set_thumbnail(url=member.avatar_url)

                # Sending the embed to the demotion channel
                bot.loop.create_task(demotion_channel.send(embed=infract_embed))

                # Log the infraction in the database
                infraction_doc = {
                    "guild_id": guild.id,
                    "member_id": member.id,
                    "type": "demotion",
                    "approver_id": current_user.id,
                    "reason": reason,
                    "rank": rank,
                    "punishment": punishment,
                    "date": datetime.datetime.now(),
                    "case": count + 1
                }
                bot.loop.create_task(bot.infraction_log.insert_one(infraction_doc))

        flash("Members demoted successfully.")
        return redirect(url_for("guild", guild_id=guild_id))

    else:
        # Render the mass demotion form
        members = guild.members
        roles = guild.roles
        return render_template("massdemote.html", guild=guild, members=members, roles=roles)

def run_production():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Server running on http://localhost:80 and http://{local_ip}:80")
    serve(app, host='0.0.0.0', port=80)

if __name__ == "__main__":
    run_production()
