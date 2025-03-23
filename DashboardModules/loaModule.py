from flask import render_template, redirect, url_for, request, flash, Blueprint, session
from flask_login import login_required, current_user
from cyni import bot
from pymongo import MongoClient
import os
import requests
from dotenv import load_dotenv

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client["cyni"] if os.getenv("PRODUCTION_TOKEN") else mongo_client["dev"]

loa_route = Blueprint('loa_module', __name__)
BOT_TOKEN = os.getenv("PRODUCTION_TOKEN") if os.getenv("PRODUCTION_TOKEN") else os.getenv("DEV_TOKEN")

@loa_route.route('/loa/<guild_id>/view/all', methods=['GET'])
@login_required
def view_all_loa(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))
    
    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    management_roles = sett.get("basic_settings", {}).get("management_roles", [])
    if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles
                if management_roles) or not (guild.get_member(int(session["user_id"])).guild_permissions.manage_guild or guild.get_member(int(session["user_id"])).guild_permissions.administrator):
        return redirect(url_for("dashboard"))
    

    loa_collection = mongo_db["loa"]
    loas = loa_collection.find(
        {"guild_id": guild.id}
    )
    return render_template("loa/view_all_loa.html", loa=loas, guild=guild)

@loa_route.route('/loa/<guild_id>/view/<user_id>', methods=['GET'])
@login_required
def view_loa(guild_id, user_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))
    
    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    management_roles = sett.get("basic_settings", {}).get("management_roles", [])
    if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles
                if management_roles) or not (guild.get_member(int(session["user_id"])).guild_permissions.manage_guild or guild.get_member(int(session["user_id"])).guild_permissions.administrator):
        return redirect(url_for("dashboard"))
    
    loa_collection = mongo_db["loa"]
    loa = loa_collection.find_one(
        {"guild_id": guild.id, "user_id": int(user_id)}
    )
    return render_template("loa/view_loa.html", loa=loa, guild=guild)

@loa_route.route('/loa/<guild_id>/update/<user_id>', methods=['GET', 'POST'])
@login_required
def update_loa(guild_id, user_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash("Guild not found.", "error")
        return redirect(url_for("dashboard"))
    
    sett = mongo_db["settings"].find_one({"_id": guild.id}) or {}
    management_roles = sett.get("basic_settings", {}).get("management_roles", [])
    if not any(role in [role.id for role in guild.get_member(int(session["user_id"])).roles] for role in management_roles
                if management_roles) or not (guild.get_member(int(session["user_id"])).guild_permissions.manage_guild or guild.get_member(int(session["user_id"])).guild_permissions.administrator):
        return redirect(url_for("dashboard"))
    
    loa_collection = mongo_db["loa"]
    loa = loa_collection.find_one(
        {"guild_id": guild.id, "user_id": int(user_id)}
    )
    if request.method == "POST":
        new_status = request.form.get("status")
        loa_collection.update_one(
            {"guild_id": guild.id, "user_id": int(user_id)},
            {"$set": {"status": new_status}}
        )
        headers = {"Authorization": BOT_TOKEN}
        api_doc = {
            "guild_id": guild.id,
            "user_id": int(user_id),
            "status": new_status,
            "loa_id": loa["_id"]
        }
        response = requests.post("http://127.0.0.1:5000/loa_update", json=api_doc, headers=headers)
        if response.status_code != 200:
            flash("Failed to update LOA. Please try again later.", "error")
            return redirect(url_for("loa_module.view_all_loa", guild_id=guild.id))
        flash("LOA updated successfully.", "success")
        return redirect(url_for("loa_module.view_all_loa", guild_id=guild.id))
    return render_template("loa/update_loa.html", loa=loa, guild=guild)