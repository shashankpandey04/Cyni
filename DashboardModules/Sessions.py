from flask import render_template, redirect, url_for, request, flash, Blueprint, session
from flask_login import login_required, current_user
from dotenv import load_dotenv
from Database.Mongo import mongo_db
from utils.site_utils import check_permissions, get_guild, get_guild_member, get_guild_channels, get_guild_roles
from datetime import datetime

load_dotenv()

sessions_route = Blueprint(
    'sessions_roblox',
    __name__,
)

@sessions_route.route('/erlc/sessions/<guild_id>', methods=['GET'])
@login_required
def erlc_sessions(guild_id):
    guild = get_guild(int(guild_id))
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))

    member = get_guild_member(int(guild_id), session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))

    has_perm = check_permissions(int(guild_id), session["user_id"])
    if has_perm is False:
        flash("You need Management Roles to access this page.", "error")
        return redirect(url_for("dashboard"))

    session_embed = mongo_db["erlc_sessions_embed"].find_one(
        {
            "guild_id": int(guild_id)
        }
    )
    return render_template('erlc/sessions/index.html', user=current_user, session=session_embed, guild=guild)

@sessions_route.route('/erlc/sessions/<guild_id>/save', methods=['POST'])
@login_required
def erlc_sessions_save(guild_id):
    guild = get_guild(int(guild_id))
    if not guild:
        return {"status": "error", "message": "Guild not found or you do not have access to it."}

    member = get_guild_member(int(guild_id), session["user_id"])
    if not member:
        return {"status": "error", "message": "You do not have access to this guild."}

    has_perm = check_permissions(int(guild_id), session["user_id"])
    if has_perm is False:
        return {"status": "error", "message": "You need Management Roles to access this page."}

    data = request.get_json()
    if not data:
        return {"status": "error", "message": "No data provided."}

    mongo_db["erlc_sessions_embed"].update_one(
        {
            "guild_id": int(guild_id)
        },
        {
            "$set": {
                "embed": {
                    "embeds": data.get("embeds", []),
                    "updated_at": datetime.now(),
                    "updated_by": session["user_id"]
                }
            }
        },
        upsert=True
    )
    
    return {"status": "success", "message": "Embeds saved successfully!"}