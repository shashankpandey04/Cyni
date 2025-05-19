from flask import render_template, redirect, url_for, request, flash, Blueprint, session, jsonify
from flask_login import login_required, current_user
from cyni import bot
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import datetime

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client["cyni"] if os.getenv("PRODUCTION_TOKEN") else mongo_client["dev"]
bot_token = os.getenv("PRODUCTION_TOKEN") if os.getenv("PRODUCTION_TOKEN") else os.getenv("DEV_TOKEN")

automod = Blueprint('automod', __name__)

@automod.route('/dashboard/<guild_id>/settings/automod/raid', methods=['GET', 'POST'])
@login_required
def raid_detection(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
        
    # Get guild settings
    settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
    automod_settings = settings.get("automod_module", {})
    raid_settings = automod_settings.get("raid_detection", {})
    
    # Get all roles and channels for settings
    roles = {role.id: role.name for role in guild.roles}
    channels = {channel.id: channel.name for channel in guild.text_channels}
    
    if request.method == 'POST':
        # Process form submission
        enabled = 'enabled' in request.form
        join_threshold = int(request.form.get('join_threshold', 5))
        time_window = int(request.form.get('time_window', 10))
        action = request.form.get('action', 'kick')
        alert_channel = request.form.get('alert_channel')
        if alert_channel:
            alert_channel = int(alert_channel)
        
        # Update settings in database
        mongo_db["settings"].update_one(
            {"_id": guild_id},
            {"$set": {
                "automod_module.enabled": True,
                "automod_module.raid_detection.enabled": enabled,
                "automod_module.raid_detection.join_threshold": join_threshold,
                "automod_module.raid_detection.time_window": time_window,
                "automod_module.raid_detection.action": action,
                "automod_module.raid_detection.alert_channel": alert_channel
            }},
            upsert=True
        )
        
        flash("Raid detection settings updated successfully", "success")
        return redirect(url_for('automod.raid_detection', guild_id=guild_id))
    
    return render_template("automod/raid_detection.html", 
                          guild=guild,
                          automod_settings=automod_settings,
                          raid_settings=raid_settings,
                          roles=roles,
                          channels=channels)

@automod.route('/dashboard/<guild_id>/settings/automod/spam', methods=['GET', 'POST'])
@login_required
def spam_detection(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    
    # Get guild settings
    settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
    automod_settings = settings.get("automod_module", {})
    spam_settings = automod_settings.get("spam_detection", {})
    
    # Get all roles and channels for settings
    roles = {role.id: role.name for role in guild.roles}
    channels = {channel.id: channel.name for channel in guild.text_channels}
    
    if request.method == 'POST':
        # Process form submission
        enabled = 'enabled' in request.form
        message_threshold = int(request.form.get('message_threshold', 5))
        time_window = int(request.form.get('time_window', 3))
        action = request.form.get('action', 'mute')
        mute_duration = int(request.form.get('mute_duration', 10))
        alert_channel = request.form.get('alert_channel')
        if alert_channel:
            alert_channel = int(alert_channel)
        
        # Update settings in database
        mongo_db["settings"].update_one(
            {"_id": guild_id},
            {"$set": {
                "automod_module.enabled": True,
                "automod_module.spam_detection.enabled": enabled,
                "automod_module.spam_detection.message_threshold": message_threshold,
                "automod_module.spam_detection.time_window": time_window,
                "automod_module.spam_detection.action": action,
                "automod_module.spam_detection.mute_duration": mute_duration,
                "automod_module.spam_detection.alert_channel": alert_channel
            }},
            upsert=True
        )
        
        flash("Spam detection settings updated successfully", "success")
        return redirect(url_for('automod.spam_detection', guild_id=guild_id))
    
    return render_template("automod/spam_detection.html", 
                          guild=guild,
                          automod_settings=automod_settings,
                          spam_settings=spam_settings,
                          roles=roles,
                          channels=channels)

@automod.route('/dashboard/<guild_id>/settings/automod/keyword', methods=['GET', 'POST'])
@login_required
def custom_keyword(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    
    # Get guild settings
    settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
    automod_settings = settings.get("automod_module", {})
    keyword_settings = automod_settings.get("custom_keyword", {})
    
    # Get all roles and channels for settings
    roles = {role.id: role.name for role in guild.roles}
    channels = {channel.id: channel.name for channel in guild.text_channels}
    
    if request.method == 'POST':
        if 'add_keyword' in request.form:
            # Add new keyword
            keyword = request.form.get('keyword', '').strip().lower()
            if not keyword:
                flash("Keyword cannot be empty", "danger")
                return redirect(url_for('automod.custom_keyword', guild_id=guild_id))
                
            # Get existing keywords
            keywords = keyword_settings.get("keywords", [])
            if keyword not in keywords:
                keywords.append(keyword)
                
                # Update settings in database
                mongo_db["settings"].update_one(
                    {"_id": guild_id},
                    {"$set": {
                        "automod_module.enabled": True,
                        "automod_module.custom_keyword.enabled": True,
                        "automod_module.custom_keyword.keywords": keywords
                    }},
                    upsert=True
                )
                
                flash(f"Keyword '{keyword}' added successfully", "success")
            else:
                flash(f"Keyword '{keyword}' already exists", "warning")
            return redirect(url_for('automod.custom_keyword', guild_id=guild_id))
        
        elif 'delete_keyword' in request.form:
            # Delete keyword
            keyword = request.form.get('keyword', '')
            keywords = keyword_settings.get("keywords", [])
            if keyword in keywords:
                keywords.remove(keyword)
                
                # Update settings in database
                mongo_db["settings"].update_one(
                    {"_id": guild_id},
                    {"$set": {
                        "automod_module.custom_keyword.keywords": keywords
                    }}
                )
                
                flash(f"Keyword '{keyword}' removed successfully", "success")
            return redirect(url_for('automod.custom_keyword', guild_id=guild_id))
        
        else:
            # Update general settings
            enabled = 'enabled' in request.form
            action = request.form.get('action', 'delete')
            alert_channel = request.form.get('alert_channel')
            if alert_channel:
                alert_channel = int(alert_channel)
            
            # Update settings in database
            mongo_db["settings"].update_one(
                {"_id": guild_id},
                {"$set": {
                    "automod_module.enabled": True,
                    "automod_module.custom_keyword.enabled": enabled,
                    "automod_module.custom_keyword.action": action,
                    "automod_module.custom_keyword.alert_channel": alert_channel
                }},
                upsert=True
            )
            
            flash("Custom keyword settings updated successfully", "success")
            return redirect(url_for('automod.custom_keyword', guild_id=guild_id))
    
    return render_template("automod/custom_keyword.html", 
                          guild=guild,
                          automod_settings=automod_settings,
                          keyword_settings=keyword_settings,
                          roles=roles,
                          channels=channels)

@automod.route('/dashboard/<guild_id>/settings/automod/link', methods=['GET', 'POST'])
@login_required
def link_blocking(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    
    # Get guild settings
    settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
    automod_settings = settings.get("automod_module", {})
    link_settings = automod_settings.get("link_blocking", {})
    
    # Get all roles and channels for settings
    roles = {role.id: role.name for role in guild.roles}
    channels = {channel.id: channel.name for channel in guild.text_channels}
    
    if request.method == 'POST':
        if 'add_domain' in request.form:
            # Add new domain to whitelist/blacklist
            domain = request.form.get('domain', '').strip().lower()
            list_type = request.form.get('list_type', 'blacklist')
            
            if not domain:
                flash("Domain cannot be empty", "danger")
                return redirect(url_for('automod.link_blocking', guild_id=guild_id))
                
            # Get existing domains
            whitelist = link_settings.get("whitelist", [])
            blacklist = link_settings.get("blacklist", [])
            
            if list_type == 'whitelist' and domain not in whitelist:
                whitelist.append(domain)
            elif list_type == 'blacklist' and domain not in blacklist:
                blacklist.append(domain)
                
            # Update settings in database
            mongo_db["settings"].update_one(
                {"_id": guild_id},
                {"$set": {
                    "automod_module.enabled": True,
                    "automod_module.link_blocking.whitelist": whitelist,
                    "automod_module.link_blocking.blacklist": blacklist
                }},
                upsert=True
            )
            
            flash(f"Domain '{domain}' added to {list_type} successfully", "success")
            return redirect(url_for('automod.link_blocking', guild_id=guild_id))
        
        elif 'delete_domain' in request.form:
            # Delete domain from whitelist/blacklist
            domain = request.form.get('domain', '')
            list_type = request.form.get('list_type', 'blacklist')
            
            whitelist = link_settings.get("whitelist", [])
            blacklist = link_settings.get("blacklist", [])
            
            if list_type == 'whitelist' and domain in whitelist:
                whitelist.remove(domain)
            elif list_type == 'blacklist' and domain in blacklist:
                blacklist.remove(domain)
                
            # Update settings in database
            mongo_db["settings"].update_one(
                {"_id": guild_id},
                {"$set": {
                    "automod_module.link_blocking.whitelist": whitelist,
                    "automod_module.link_blocking.blacklist": blacklist
                }}
            )
            
            flash(f"Domain '{domain}' removed from {list_type} successfully", "success")
            return redirect(url_for('automod.link_blocking', guild_id=guild_id))
        
        else:
            # Update general settings
            enabled = 'enabled' in request.form
            block_all_links = 'block_all_links' in request.form
            block_discord_invites = 'block_discord_invites' in request.form
            whitelist_mode = 'whitelist_mode' in request.form
            action = request.form.get('action', 'delete')
            alert_channel = request.form.get('alert_channel')
            if alert_channel:
                alert_channel = int(alert_channel)
            
            # Update settings in database
            mongo_db["settings"].update_one(
                {"_id": guild_id},
                {"$set": {
                    "automod_module.enabled": True,
                    "automod_module.link_blocking.enabled": enabled,
                    "automod_module.link_blocking.block_all_links": block_all_links,
                    "automod_module.link_blocking.block_discord_invites": block_discord_invites,
                    "automod_module.link_blocking.whitelist_mode": whitelist_mode,
                    "automod_module.link_blocking.action": action,
                    "automod_module.link_blocking.alert_channel": alert_channel
                }},
                upsert=True
            )
            
            flash("Link blocking settings updated successfully", "success")
            return redirect(url_for('automod.link_blocking', guild_id=guild_id))
    
    return render_template("automod/link_blocking.html", 
                          guild=guild,
                          automod_settings=automod_settings,
                          link_settings=link_settings,
                          roles=roles,
                          channels=channels)

@automod.route('/dashboard/<guild_id>/settings/automod/exemptions', methods=['GET', 'POST'])
@login_required
def exemptions(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    
    # Get guild settings
    settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
    automod_settings = settings.get("automod_module", {})
    exempt_settings = automod_settings.get("exemptions", {})
    
    # Get all roles and channels for settings
    roles = {role.id: role.name for role in guild.roles}
    channels = {channel.id: channel.name for channel in guild.text_channels}
    
    if request.method == 'POST':
        exempt_roles = request.form.getlist('exempt_roles')
        exempt_channels = request.form.getlist('exempt_channels')
        
        # Convert to integers
        exempt_roles = [int(role_id) for role_id in exempt_roles]
        exempt_channels = [int(channel_id) for channel_id in exempt_channels]
        
        # Update settings in database
        mongo_db["settings"].update_one(
            {"_id": guild_id},
            {"$set": {
                "automod_module.enabled": True,
                "automod_module.exemptions.roles": exempt_roles,
                "automod_module.exemptions.channels": exempt_channels
            }},
            upsert=True
        )
        
        flash("Exemption settings updated successfully", "success")
        return redirect(url_for('automod.exemptions', guild_id=guild_id))
    
    return render_template("automod/exemptions.html", 
                          guild=guild,
                          automod_settings=automod_settings,
                          exempt_settings=exempt_settings,
                          roles=roles,
                          channels=channels)
