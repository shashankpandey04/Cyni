from flask import render_template, redirect, url_for, request, flash, Blueprint, session, jsonify
from flask_login import login_required, current_user
import os
import requests
from dotenv import load_dotenv
from Database.Mongo import mongo_db
from utils.site_utils import check_permissions, get_guild, get_guild_member, get_guild_channels, get_guild_roles

load_dotenv()

api_token = os.getenv("API_TOKEN", "default_api_token")

loa_route = Blueprint('loa_module', __name__)
BOT_TOKEN = os.getenv("PRODUCTION_TOKEN") or os.getenv("PREMIUM_TOKEN") or os.getenv("DEV_TOKEN")

@loa_route.route('/dashboard/<guild_id>/loa', methods=['GET'])
@login_required
def loa_homepage(guild_id):
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
        flash("You need Management Roles to access this page.", "error")
        return redirect(url_for("dashboard"))

    loa_collection = mongo_db["loa"]
    loas = loa_collection.find(
        {"guild_id": guild["id"]}
    )
    guild_data = mongo_db["settings"].find_one({"_id": guild["id"]}) or {}
    return render_template("loa/index.html", loa=loas, guild=guild, guild_data=guild_data)

@loa_route.route('/dashboard/<guild_id>/loa/<user_id>', methods=['GET'])
@login_required
def view_loa(guild_id, user_id):
    guild = get_guild(int(guild_id))
    if not guild:
        return {"error": "Guild not found."}, 404
    
    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        return {"error": "Member not found in the guild."}, 404

    has_permission = check_permissions(guild.id, session["user_id"])
    if not has_permission:
        return {"error": "You do not have permission to view this LOA."}, 403

    loa_collection = mongo_db["loa"]
    loa = loa_collection.find_one(
        {"guild_id": guild.id, "user_id": int(user_id)}
    )
    if not loa:
        return {"error": "LOA not found."}, 404

    display_name = member["display_name"] if member else str(loa["user_id"])

    return jsonify({
        "guild_id": str(loa["guild_id"]),
        "user_id": str(loa["user_id"]),
        "display_name": display_name,
        "accepted": loa.get("accepted", False),
        "denied": loa.get("denied", False),
        "voided": loa.get("voided", False),
        "expired": loa.get("expired", False),
        "type": loa.get("type", "loa"),
        "reason": loa.get("reason", ""),
        "start": loa.get("start", ""),
        "expiry": loa.get("expiry", ""),
        "dm_sent": loa.get("dm_sent", False)
    }), 200

@loa_route.route('/loa/<guild_id>/update/<user_id>', methods=['POST'])
@login_required
def update_loa(guild_id, user_id):
    guild = get_guild(int(guild_id))
    if not guild:
        return {"error": "Guild not found."}, 404
    
    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        return {"error": "You are not a member of this guild."}, 404

    has_permission = check_permissions(guild.id, session["user_id"])
    if not has_permission:
        return {"error": "You do not have permission to update this LOA."}, 403

    loa = mongo_db["loa"].find_one({"guild_id": int(guild_id), "user_id": int(user_id)})
    if loa is None:
        return {"error": "COPE not found."}, 404

    if not request.form.get("status"):
        return {"error": "Status is required."}, 400

    new_status = request.form.get("status")
    update_fields = {
        "accepted": False,
        "denied": False,
        "voided": False,
        "expired": False
    }
    if new_status in update_fields:
        if new_status == "expired":
            update_fields.pop("accepted")
        update_fields[new_status] = True
    else:
        return {"error": "Invalid status."}, 400
    mongo_db["loa"].update_one(
        {"guild_id": guild.id, "user_id": int(user_id)},
        {"$set": update_fields}
    )
    headers = {"Authorization": api_token}
    api_doc = {
        "guild_id": int(guild.id),
        "user_id": int(user_id),
        "status": new_status,
        "id": str(loa["_id"]),
        "type": loa.get("type", "loa"),
        "expiry": loa.get("expiry", ""),
    }
    response = requests.post("http://127.0.0.1:5000/loa_update", json=api_doc, headers=headers)
    if response.status_code != 200:
        return {"error": "Failed to update LOA in the API."}, 500
    return {"message": "LOA updated successfully."}, 200
    