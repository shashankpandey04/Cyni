from flask import render_template, redirect, url_for, request, flash, Blueprint, session
from flask_login import login_required
from cyni import bot
import os
from dotenv import load_dotenv
import datetime
import uuid
import requests
from Database.Mongo import mongo_db

load_dotenv()

api_token = os.getenv("API_TOKEN", "default_api_token")

ticket_module = Blueprint('ticket_module', __name__)

@ticket_module.route('/dashboard/<guild_id>/settings/ticket', methods=['GET', 'POST'])
@login_required
def ticket_settings(guild_id):
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
    ticket_settings = settings.get("ticket_module", {})

    ticket_categories = list(mongo_db["ticket_categories"].find({"guild_id": guild_id}))

    channels = {channel.id: channel.name for channel in guild.text_channels}

    roles = {role.id: role.name for role in guild.roles}
    
    discord_categories = {category.id: category.name for category in guild.categories}
    
    return render_template("tickets/main.html", 
                          guild=guild,
                          ticket_settings=ticket_settings,
                          ticket_categories=ticket_categories,
                          channels=channels,
                          roles=roles,
                          discord_categories=discord_categories)

@ticket_module.route('/dashboard/<guild_id>/settings/ticket/category/new', methods=['GET', 'POST'])
@login_required
def new_ticket_category(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
    
    existing_categories = list(mongo_db["ticket_categories"].find({"guild_id": guild_id}))
    premium = mongo_db["premium"].find_one({"guild_id": int(guild_id)})
    if len(existing_categories) >= 1 and not premium:
        flash("Upgrade to CYNI Premium to create more than one ticket category", "danger")
        return redirect(url_for('ticket_module.ticket_settings', guild_id=guild_id))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    
    channels = {channel.id: channel.name for channel in guild.text_channels}
    roles = {role.id: role.name for role in guild.roles}
    categories = {category.id: category.name for category in guild.categories}
    
    if request.method == 'POST':
        category_name = request.form.get('category_name')
        category_description = request.form.get('category_description')
        emoji = request.form.get('emoji', '🎫')
        ticket_channel = int(request.form.get('ticket_channel'))
        transcript_channel = request.form.get('transcript_channel')
        if transcript_channel:
            transcript_channel = int(transcript_channel)
        discord_category = request.form.get('discord_category')
        if discord_category:
            discord_category = int(discord_category)
        support_roles = request.form.getlist('support_roles')

        support_roles = [int(role_id) for role_id in support_roles]

        embed_title = request.form.get('embed_title', 'Support Ticket')
        embed_description = request.form.get('embed_description', 'Click the button below to create a ticket')
        embed_color = request.form.get('embed_color', '#5865F2').lstrip('#')
        embed_color = int(embed_color, 16)
        
        category_id = str(uuid.uuid4())

        ticket_category = {
            "_id": category_id,
            "guild_id": guild_id,
            "name": category_name,
            "description": category_description,
            "emoji": emoji,
            "ticket_channel": ticket_channel,
            "transcript_channel": transcript_channel,
            "discord_category": discord_category,
            "support_roles": support_roles,
            "created_at": datetime.datetime.now(),
            "embed": {
                "title": embed_title,
                "description": embed_description,
                "color": embed_color
            }
        }
        
        mongo_db["ticket_categories"].insert_one(ticket_category)
        flash(f"Ticket category '{category_name}' created successfully", "success")

        mongo_db["settings"].update_one(
            {"_id": guild_id},
            {"$set": {"ticket_module.enabled": True}},
            upsert=True
        )
        
        return redirect(url_for('ticket_module.ticket_settings', guild_id=guild_id))
    
    return render_template("tickets/new_category.html", guild=guild, channels=channels, roles=roles, categories=categories)

@ticket_module.route('/dashboard/<guild_id>/settings/ticket/category/<category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket_category(guild_id, category_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))

    category = mongo_db["ticket_categories"].find_one({"_id": category_id, "guild_id": guild_id})
    if not category:
        flash("Ticket category not found", "danger")
        return redirect(url_for('ticket_module.ticket_settings', guild_id=guild_id))
    
    channels = {channel.id: channel.name for channel in guild.text_channels}
    roles = {role.id: role.name for role in guild.roles}
    categories = {category.id: category.name for category in guild.categories}
    
    if request.method == 'POST':
        category_name = request.form.get('category_name')
        category_description = request.form.get('category_description')
        emoji = request.form.get('emoji', '🎫')
        ticket_channel = int(request.form.get('ticket_channel'))
        transcript_channel = request.form.get('transcript_channel')
        if transcript_channel:
            transcript_channel = int(transcript_channel)
        discord_category = request.form.get('discord_category')
        if discord_category:
            discord_category = int(discord_category)
        support_roles = request.form.getlist('support_roles')
        
        support_roles = [int(role_id) for role_id in support_roles]
        
        embed_title = request.form.get('embed_title')
        embed_description = request.form.get('embed_description')
        embed_color = request.form.get('embed_color', '#5865F2').lstrip('#')
        embed_color = int(embed_color, 16)
        
        mongo_db["ticket_categories"].update_one(
            {"_id": category_id},
            {"$set": {
                "name": category_name,
                "description": category_description,
                "emoji": emoji,
                "ticket_channel": ticket_channel,
                "transcript_channel": transcript_channel,
                "discord_category": discord_category,
                "support_roles": support_roles,
                "embed": {
                    "title": embed_title,
                    "description": embed_description,
                    "color": embed_color
                }
            }}
        )
        
        flash(f"Ticket category '{category_name}' updated successfully", "success")
        return redirect(url_for('ticket_module.ticket_settings', guild_id=guild_id))
    
    return render_template("tickets/edit_category.html", 
                          guild=guild, 
                          category=category, 
                          channels=channels, 
                          roles=roles,
                          categories=categories)

@ticket_module.route('/dashboard/<guild_id>/settings/ticket/category/<category_id>/delete', methods=['POST'])
@login_required
def delete_ticket_category(guild_id, category_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    
    # Delete the ticket category
    result = mongo_db["ticket_categories"].delete_one({"_id": category_id, "guild_id": guild_id})
    
    if result.deleted_count > 0:
        flash("Ticket category deleted successfully", "success")
    else:
        flash("Failed to delete ticket category", "danger")
    
    return redirect(url_for('ticket_module.ticket_settings', guild_id=guild_id))

@ticket_module.route('/dashboard/<guild_id>/settings/ticket/category/<category_id>/send', methods=['POST'])
@login_required
def send_ticket_embed(guild_id, category_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    
    # Get the ticket category
    category = mongo_db["ticket_categories"].find_one({"_id": category_id, "guild_id": guild_id})
    if not category:
        flash("Ticket category not found", "danger")
        return redirect(url_for('ticket_module.ticket_settings', guild_id=guild_id))
    
    # Send data to the API to create and send the embed
    data = {
        "guild_id": guild_id,
        "category_id": category_id
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:5000/send_ticket_embed",
            headers={"Authorization": api_token},
            json=data
        )
        
        if response.status_code == 200:
            flash("Ticket embed sent successfully", "success")
        else:
            flash(f"Failed to send ticket embed: {response.text}", "danger")
    except Exception as e:
        flash(f"Error sending ticket embed: {str(e)}", "danger")
    
    return redirect(url_for('ticket_module.ticket_settings', guild_id=guild_id))

@ticket_module.route('/dashboard/<guild_id>/tickets', methods=['GET'])
@login_required
def view_tickets(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member:
        flash("You are not a member of this guild", "danger")
        return redirect(url_for('dashboard'))
    
    # Check if user has permission to view tickets
    settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
    ticket_settings = settings.get("ticket_module", {})
    
    has_permission = False
    
    # Check if user is admin or has manage_guild permission
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        has_permission = True
    else:
        # Check if user has any of the support roles from any ticket category
        categories = list(mongo_db["ticket_categories"].find({"guild_id": guild_id}))
        for category in categories:
            if any(role.id in category.get("support_roles", []) for role in member.roles):
                has_permission = True
                break
    
    if not has_permission:
        flash("You don't have permission to view tickets", "danger")
        return redirect(url_for('dashboard'))
    
    tickets = list(mongo_db["tickets"].find({"guild_id": guild_id}).sort("created_at", -1))
    
    return render_template("tickets/view_tickets.html", guild=guild, tickets=tickets)

@ticket_module.route('/transcripts/<guild_id>/<transcript_id>', methods=['GET'])
def view_transcript(guild_id, transcript_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
    
    member = guild.get_member(int(session["user_id"]))
    if not member:
        flash("You are not a member of this guild", "danger")
        return redirect(url_for('dashboard'))
    
    has_permission = False
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        has_permission = True
    else:
        categories = list(mongo_db["ticket_categories"].find({"guild_id": guild_id}))
        for category in categories:
            if any(role.id in category.get("support_roles", []) for role in member.roles):
                has_permission = True
                break
    if not has_permission:
        flash("You don't have permission to view transcripts", "danger")
        return redirect(url_for('dashboard'))
    
    transcript = mongo_db["ticket_transcripts"].find_one({"_id": transcript_id})
    if not transcript:
        flash("Transcript not found", "danger")
        return redirect(url_for('dashboard'))
    
    ticket = mongo_db["tickets"].find_one({"_id": transcript.get("ticket_id")})
    
    guild = bot.get_guild(transcript.get("guild_id"))
    guild_name = guild.name if guild else "Unknown Server"
    
    messages = transcript.get("messages", [])
    
    return render_template(
        "tickets/transcript.html", 
        transcript=transcript, 
        ticket=ticket, 
        messages=messages, 
        guild_name=guild_name,
        guild=guild
    )

@ticket_module.route('/transcripts/<guild_id>', methods=['GET'])
@login_required
def view_guild_transcripts(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member:
        flash("You are not a member of this guild", "danger")
        return redirect(url_for('dashboard'))

    settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
    
    has_permission = False
    
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        has_permission = True
    else:
        categories = list(mongo_db["ticket_categories"].find({"guild_id": guild_id}))
        for category in categories:
            if any(role.id in category.get("support_roles", []) for role in member.roles):
                has_permission = True
                break
    
    if not has_permission:
        flash("You don't have permission to view tickets", "danger")
        return redirect(url_for('dashboard'))
    
    transcripts = list(mongo_db["ticket_transcripts"].find({"guild_id": guild_id}).sort("created_at", -1))
    
    return render_template("tickets/view_transcripts.html", guild=guild, transcripts=transcripts)