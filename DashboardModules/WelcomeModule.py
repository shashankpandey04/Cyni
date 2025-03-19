from flask import render_template, redirect, url_for, request, flash, Blueprint, session
from flask_login import login_required, current_user
from cyni import bot
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client["cyni"] if os.getenv("PRODUCTION_TOKEN") else mongo_client["dev"]

welcome_route = Blueprint('welcome_module', __name__)

@welcome_route.route('/dashboard/<guild_id>/settings/welcome', methods=['GET', 'POST'])
@login_required
def welcome(guild_id):
    guild = bot.get_guild(int(guild_id))
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
    
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        return "You do not have the required permissions to access this page.", 403
    
    guild_data = mongo_db["settings"].find_one({"_id": guild.id}) or {'_id': guild.id, 'welcome_module': {'welcome_message': None,'welcome_channel': None,'welcome_role': None}}
    if request.method == 'POST':
        welcome_message = request.form.get('welcome_message')
        welcome_channel = request.form.get('welcome_channel')
        welcome_role = request.form.get('welcome_role')
        
        guild_data['welcome_module']['welcome_message'] = welcome_message
        guild_data['welcome_module']['welcome_channel'] = welcome_channel
        guild_data['welcome_module']['welcome_role'] = welcome_role
        
        mongo_db["settings"].update_one({"_id": guild.id}, {"$set": {'welcome_module': {'welcome_message': welcome_message,'welcome_channel': welcome_channel,'welcome_role': welcome_role}}}, upsert=True)
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('welcome_module.welcome', guild_id=guild.id))

    channels = {channel.id: channel.name for channel in guild.channels if channel.type == 0}
    roles = {role.id: role.name for role in guild.roles}
    return render_template('welcome_module/index.html', user=current_user, guild=guild, guild_data=guild_data, channels=channels, roles=roles)