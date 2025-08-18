from flask import render_template, redirect, url_for, request, flash, Blueprint, session, jsonify
from flask_login import login_required, current_user
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from Database.Mongo import mongo_db
from utils.site_utils import get_guild, get_guild_member, get_guild_channels, get_guild_roles, check_permissions

load_dotenv()

automod = Blueprint('automod', __name__)

@automod.route('/dashboard/<guild_id>/settings/automod', methods=['GET', 'POST'])
@login_required
def automod_settings(guild_id):
    guild_id = int(guild_id)
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))
    
    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))

    settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
    is_premium = mongo_db['premium'].find_one({"_id": guild_id}) is not None
    
    automod_settings = settings.get("automod_module", {})
    
    roles = get_guild_roles(guild_id)
    if not roles:
        flash("There was an error fetching roles for this guild.", "error")
        return redirect(url_for("guild", guild_id=guild_id))

    channels = get_guild_channels(guild_id)
    if not channels:
        flash("No channels found in this guild.", "error")
        return redirect(url_for("guild", guild_id=guild_id))

    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm is False:
        flash("You need Management Roles to access this page.", "error")
        return redirect(url_for("dashboard"))

    if request.method == 'POST':
        action_type = request.form.get('action_type')

        if request.form.get('add_keyword') == '1':
            action_type = 'custom_keyword'
        elif request.form.get('add_domain') == '1':
            action_type = 'link_blocking'
        elif request.form.get('delete_keyword') == '1':
            action_type = 'custom_keyword'
        elif request.form.get('delete_domain') == '1':
            action_type = 'link_blocking'
        
        # If no specific action_type, determine from form data with meaningful changes
        if not action_type or action_type == 'None':
            # Check which section has actual meaningful data/changes
            if ('raid_enabled' in request.form and request.form.get('raid_enabled')) or \
               (request.form.get('raid_alert_channel') and request.form.get('raid_alert_channel').strip()):
                action_type = 'raid_detection'
            elif ('spam_enabled' in request.form and request.form.get('spam_enabled')) or \
                 (request.form.get('spam_alert_channel') and request.form.get('spam_alert_channel').strip()):
                action_type = 'spam_detection'
            elif ('keyword_enabled' in request.form and request.form.get('keyword_enabled')) or \
                 (request.form.get('keyword_alert_channel') and request.form.get('keyword_alert_channel').strip()):
                action_type = 'custom_keyword'
            elif ('link_enabled' in request.form and request.form.get('link_enabled')) or \
                 (request.form.get('link_alert_channel') and request.form.get('link_alert_channel').strip()):
                action_type = 'link_blocking'
            elif request.form.getlist('exempt_roles') or request.form.getlist('exempt_channels'):
                action_type = 'exemptions'
            elif ('vanity_enabled' in request.form and request.form.get('vanity_enabled')) or \
                 request.form.getlist('vanity_exempt_roles') or \
                 (request.form.get('vanity_exempt_users') and request.form.get('vanity_exempt_users').strip()):
                action_type = 'vanity_protection'

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
            if not is_premium:
                flash('Vanity protection is only available for premium servers.', 'warning')
                return redirect(url_for('automod.automod_settings', guild_id=guild_id))
            # Only guild owner can modify vanity protection settings
            if guild.owner_id != int(session["user_id"]):
                flash("Only the guild owner can modify vanity protection settings.", "danger")
                return redirect(url_for('automod.automod_settings', guild_id=guild_id))
            _handle_vanity_protection_update(guild_id, request.form)
        else:
            print(f"Unknown action_type: {action_type}")
            flash('Invalid action type', 'error')
        
        return redirect(url_for('automod.automod_settings', guild_id=guild_id))
        
    # GET request - show the form
    settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
    automod_settings = settings.get("automod_module", {})
    
    return render_template("automod/automod_settings.html", 
                          guild=guild,
                          automod_settings=automod_settings,
                          roles=roles,
                          channels=channels,
                          is_premium=is_premium,
                          is_owner=guild["owner_id"] == int(session["user_id"]))

@automod.route('/dashboard/<guild_id>/settings/automod/toggle', methods=['POST'])
@login_required
def automod_toggle(guild_id):
    """AJAX endpoint for handling toggle changes without page refresh"""
    guild_id = int(guild_id)
    guild = get_guild(guild_id)
    if not guild:
        return jsonify({'success': False, 'message': 'Guild not found'}), 404
    
    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        return jsonify({'success': False, 'message': 'No permission'}), 403


    settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
    is_premium = settings.get("premium", False)
    
    try:
        action_type = request.json.get('action_type')
        enabled = request.json.get('enabled', False)
        
        # Handle vanity protection premium check
        if action_type == 'vanity_protection':
            if not is_premium:
                return jsonify({'success': False, 'message': 'Vanity protection requires premium'}), 403
            if guild.owner_id != int(session["user_id"]):
                return jsonify({'success': False, 'message': 'Only guild owner can modify vanity protection'}), 403
        
        # Update the specific toggle in database
        update_path = f"automod_module.{action_type}.enabled"
        mongo_db["settings"].update_one(
            {"_id": guild_id},
            {"$set": {
                "automod_module.enabled": True,
                update_path: enabled
            }},
            upsert=True
        )
        
        return jsonify({
            'success': True, 
            'message': f'{action_type.replace("_", " ").title()} {"enabled" if enabled else "disabled"} successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

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
    print(f"DEBUG: _handle_link_blocking_update called with form_data: {dict(form_data)}")
    link_settings = automod_settings.get("link_blocking", {})
    
    if form_data.get('add_domain') == '1':
        print("DEBUG: Handling add_domain")
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
    
    elif form_data.get('delete_domain') == '1':
        print("DEBUG: Handling delete_domain")
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
        print("DEBUG: Handling general link blocking settings update")
        enabled = 'link_enabled' in form_data
        block_all_links = 'block_all_links' in form_data
        block_discord_invites = 'block_discord_invites' in form_data
        whitelist_mode = 'whitelist_mode' in form_data
        action = form_data.get('link_action', 'delete')
        alert_channel = form_data.get('link_alert_channel')
        if alert_channel:
            alert_channel = int(alert_channel)
        
        print(f"DEBUG: Settings to update - enabled: {enabled}, action: {action}, alert_channel: {alert_channel}")

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
        
        print("DEBUG: Database update completed")
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
