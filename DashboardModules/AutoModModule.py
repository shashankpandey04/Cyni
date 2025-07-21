from flask import render_template, redirect, url_for, request, flash, Blueprint, session, jsonify
from flask_login import login_required, current_user
from cyni import bot
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from Database.Mongo import mongo_db

load_dotenv()
bot_token = os.getenv("PRODUCTION_TOKEN") if os.getenv("PRODUCTION_TOKEN") else os.getenv("DEV_TOKEN")

automod = Blueprint('automod', __name__)

@automod.route('/dashboard/<guild_id>/settings/automod', methods=['GET', 'POST'])
@login_required
def automod_settings(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))

    settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
    is_premium = settings.get("premium", False)
    
    if request.headers.get('Content-Type') == 'application/json' and not is_premium:
        return jsonify({"error": "Premium required", "premium": False}), 403
    
    automod_settings = settings.get("automod_module", {})
    
    roles = {role.id: role.name for role in guild.roles if role.name != "@everyone"}
    channels = {channel.id: channel.name for channel in guild.text_channels}
    
    if request.method == 'POST':
        if not is_premium:
            flash('This feature is only available for premium servers.', 'warning')
            return redirect(url_for('automod.automod_settings', guild_id=guild_id))
        
        action_type = request.form.get('action_type')

        if action_type == 'raid_detection':
            _handle_raid_detection_update(guild_id, request.form)
        elif action_type == 'spam_detection':
            _handle_spam_detection_update(guild_id, request.form)
        elif action_type == 'custom_keyword':
            _handle_custom_keyword_update(guild_id, request.form, automod_settings)
        elif action_type == 'link_blocking':
            _handle_link_blocking_update(guild_id, request.form, automod_settings)
        elif action_type == 'exemptions':
            _handle_exemptions_update(guild_id, request.form)
        elif action_type == 'vanity_protection':
            if guild.owner_id != int(session["user_id"]):
                flash("Only the guild owner can modify vanity protection settings.", "danger")
                return redirect(url_for('automod.automod_settings', guild_id=guild_id))
            _handle_vanity_protection_update(guild_id, request.form)
        
        settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
        automod_settings = settings.get("automod_module", {})
    
    return render_template("automod/automod_settings.html", 
                          guild=guild,
                          automod_settings=automod_settings,
                          roles=roles,
                          channels=channels,
                          is_premium=is_premium,
                          is_owner=guild.owner_id == int(session["user_id"]))

def _handle_raid_detection_update(guild_id, form_data):
    """Handle raid detection settings update"""
    enabled = 'raid_enabled' in form_data
    join_threshold = int(form_data.get('raid_join_threshold', 5))
    time_window = int(form_data.get('raid_time_window', 10))
    action = form_data.get('raid_action', 'kick')
    alert_channel = form_data.get('raid_alert_channel')
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

def _handle_spam_detection_update(guild_id, form_data):
    """Handle spam detection settings update"""
    enabled = 'spam_enabled' in form_data
    message_threshold = int(form_data.get('spam_message_threshold', 5))
    time_window = int(form_data.get('spam_time_window', 3))
    action = form_data.get('spam_action', 'mute')
    mute_duration = int(form_data.get('spam_mute_duration', 10))
    alert_channel = form_data.get('spam_alert_channel')
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

def _handle_custom_keyword_update(guild_id, form_data, automod_settings):
    """Handle custom keyword settings update"""
    keyword_settings = automod_settings.get("custom_keyword", {})
    
    if 'add_keyword' in form_data:
        # Add new keyword
        keyword = form_data.get('new_keyword', '').strip().lower()
        if not keyword:
            flash("Keyword cannot be empty", "danger")
            return
            
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
    
    elif 'delete_keyword' in form_data:
        # Delete keyword
        keyword = form_data.get('keyword_to_delete', '')
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
    
    else:
        # Update general settings
        enabled = 'keyword_enabled' in form_data
        action = form_data.get('keyword_action', 'delete')
        alert_channel = form_data.get('keyword_alert_channel')
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

def _handle_link_blocking_update(guild_id, form_data, automod_settings):
    """Handle link blocking settings update"""
    link_settings = automod_settings.get("link_blocking", {})
    
    if 'add_domain' in form_data:
        # Add new domain to whitelist/blacklist
        domain = form_data.get('new_domain', '').strip().lower()
        list_type = form_data.get('domain_list_type', 'blacklist')
        
        if not domain:
            flash("Domain cannot be empty", "danger")
            return
            
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
    
    elif 'delete_domain' in form_data:
        # Delete domain from whitelist/blacklist
        domain = form_data.get('domain_to_delete', '')
        list_type = form_data.get('domain_delete_type', 'blacklist')
        
        whitelist = link_settings.get("whitelist", [])
        blacklist = link_settings.get("blacklist", [])
        
        if list_type == 'whitelist' and domain in whitelist:
            whitelist.remove(domain)
        elif list_type == 'blacklist' and domain in blacklist:
            blacklist.remove(domain)

        mongo_db["settings"].update_one(
            {"_id": guild_id},
            {"$set": {
                "automod_module.link_blocking.whitelist": whitelist,
                "automod_module.link_blocking.blacklist": blacklist
            }}
        )
        
        flash(f"Domain '{domain}' removed from {list_type} successfully", "success")
    
    else:
        enabled = 'link_enabled' in form_data
        block_all_links = 'block_all_links' in form_data
        block_discord_invites = 'block_discord_invites' in form_data
        whitelist_mode = 'whitelist_mode' in form_data
        action = form_data.get('link_action', 'delete')
        alert_channel = form_data.get('link_alert_channel')
        if alert_channel:
            alert_channel = int(alert_channel)

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

def _handle_exemptions_update(guild_id, form_data):
    """Handle exemptions settings update"""
    exempt_roles = form_data.getlist('exempt_roles')
    exempt_channels = form_data.getlist('exempt_channels')
    
    # Convert to integers
    exempt_roles = [int(role_id) for role_id in exempt_roles if role_id]
    exempt_channels = [int(channel_id) for channel_id in exempt_channels if channel_id]
    
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

def _handle_vanity_protection_update(guild_id, form_data):
    """Handle vanity protection settings update"""
    enabled = 'vanity_enabled' in form_data
    exempt_roles = form_data.getlist('vanity_exempt_roles')
    exempt_users_input = form_data.get('vanity_exempt_users', '').strip()

    exempt_roles = [int(role_id) for role_id in exempt_roles if role_id]

    exempt_users = []
    if exempt_users_input:
        try:
            exempt_users = [int(user_id.strip()) for user_id in exempt_users_input.split(',') if user_id.strip()]
        except ValueError:
            flash("Invalid user ID format. Please use comma-separated user IDs.", "danger")
            return
    
    mongo_db["settings"].update_one(
        {"_id": guild_id},
        {"$set": {
            "automod_module.enabled": True,
            "automod_module.vanity_protection.enabled": enabled,
            "automod_module.vanity_protection.exempt_roles": exempt_roles,
            "automod_module.vanity_protection.exempt_users": exempt_users
        }},
        upsert=True
    )
    
    flash("Vanity protection settings updated successfully", "success")
