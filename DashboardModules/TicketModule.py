from flask import render_template, redirect, url_for, request, flash, Blueprint, session
from flask_login import login_required
from cyni import bot
import os
from dotenv import load_dotenv
import datetime
import uuid
import requests
from Database.Mongo import mongo_db
from utils.site_utils import (
    check_permissions, get_guild, 
    get_guild_member, get_guild_channels, 
    get_guild_roles, get_guild_categories,
    get_api_url_for_guild, get_guild_emojis
)
from bson import ObjectId

load_dotenv()

api_token = os.getenv("API_TOKEN", "default_api_token")

CYNI_API_BASE_URL = os.getenv("CYNI_API_BASE_URL")
CYNI_PREMIUM_API_URL = os.getenv("CYNI_PREMIUM_API_URL")

ticket_module = Blueprint('ticket_module', __name__)

@ticket_module.route('/dashboard/<guild_id>/settings/ticket', methods=['GET', 'POST'])
@login_required
def ticket_settings(guild_id):
    guild_id = int(guild_id)
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
        
    settings = mongo_db["settings"].find_one({"_id": guild_id}) or {}
    ticket_settings = settings.get("ticket_module", {})

    ticket_categories = list(mongo_db["ticket_categories"].find({"guild_id": guild_id}))

    channels = get_guild_channels(guild_id)

    roles = get_guild_roles(guild_id)

    discord_categories = get_guild_categories(guild_id)

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

    existing_categories = list(mongo_db["ticket_categories"].find({"guild_id": int(guild_id)}))
    premium = mongo_db["premium"].find_one({"_id": int(guild_id)})
    if len(existing_categories) >= 1 and not premium:
        flash("Upgrade to CYNI Premium to create more than one ticket category", "danger")
        return redirect(url_for('ticket_module.ticket_settings', guild_id=guild_id))

    channels = get_guild_channels(guild_id)
    roles = get_guild_roles(guild_id)
    categories = get_guild_categories(guild_id)
    emojis = get_guild_emojis(guild_id)

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

        welcome_embed_title = request.form.get('welcome_embed_title', 'Welcome to Support')
        welcome_embed_description = request.form.get('welcome_embed_description', 'Thanks for reaching out! A member of our support team will be with you shortly.')
        welcome_embed_color = request.form.get('welcome_embed_color', '#5865F2').lstrip('#')
        welcome_embed_color = int(welcome_embed_color, 16)

        naming_scheme = request.form.get('naming_scheme', '{ticket_id}-{username}')

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
            },
            "welcome_embed": {
                "title": welcome_embed_title,
                "description": welcome_embed_description,
                "color": welcome_embed_color
            },
            "naming_scheme": naming_scheme
        }
        
        mongo_db["ticket_categories"].insert_one(ticket_category)
        flash(f"Ticket category '{category_name}' created successfully", "success")

        mongo_db["settings"].update_one(
            {"_id": guild_id},
            {"$set": {"ticket_module.enabled": True}},
            upsert=True
        )
        
        return redirect(url_for('ticket_module.ticket_settings', guild_id=guild_id))
    
    return render_template("tickets/new_category.html", guild=guild, channels=channels, roles=roles, categories=categories, emojis=emojis)

@ticket_module.route('/dashboard/<guild_id>/settings/ticket/category/<category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket_category(guild_id, category_id):
    guild_id = int(guild_id)
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

    category = mongo_db["ticket_categories"].find_one({"_id": category_id, "guild_id": guild_id})
    if not category:
        flash(f"Ticket category {category_id} not found", "danger")
        return redirect(url_for('ticket_module.ticket_settings', guild_id=guild_id))

    channels = get_guild_channels(guild_id)
    roles = get_guild_roles(guild_id)
    categories = get_guild_categories(guild_id)

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

        welcome_embed_title = request.form.get('welcome_embed_title', 'Welcome to Support')
        welcome_embed_description = request.form.get('welcome_embed_description', 'Thanks for reaching out! A member of our support team will be with you shortly.')
        welcome_embed_color = request.form.get('welcome_embed_color', '#5865F2').lstrip('#')
        welcome_embed_color = int(welcome_embed_color, 16)

        naming_scheme = request.form.get('naming_scheme', '{ticket_id}-{username}')
        
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
                },
                "welcome_embed": {
                    "title": welcome_embed_title,
                    "description": welcome_embed_description,
                    "color": welcome_embed_color
                },
                "naming_scheme": naming_scheme
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
    
    # Send data to the API to create and send the embed
    data = {
        "guild_id": guild_id,
        "category_id": category_id
    }

    api_url = get_api_url_for_guild(guild_id)
    if not api_url:
        flash("API URL for guild not found.", "danger")
        return redirect(url_for('ticket_module.ticket_settings', guild_id=guild_id))

    try:
        response = requests.post(
            f"{api_url}/send_ticket_embed",
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
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))
    
    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if not has_perm:
        flash("You don't have roles required to view this category of tickets", "danger")
        return redirect(url_for('dashboard'))
    
    tickets = list(mongo_db["tickets"].find({"guild_id": guild_id}).sort("created_at", -1))
    
    return render_template("tickets/view_tickets.html", guild=guild, tickets=tickets)

@ticket_module.route('/transcripts/<ticket_id>', methods=['GET'])
def view_transcript(ticket_id):

    transcript_doc = mongo_db["ticket_transcripts"].find_one({"ticket_id": ticket_id})
    if not transcript_doc:
        flash(f"Transcript {ticket_id} not found", "danger")
        return redirect(url_for('dashboard'))

    guild_id = int(transcript_doc.get("guild_id"))
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))
    
    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_perm = check_permissions(guild_id, session["user_id"])
    if not has_perm:
        flash("You don't have permission to view this transcript", "danger")
        return redirect(url_for('dashboard'))

    ticket = mongo_db["tickets"].find_one({"_id": transcript_doc.get("ticket_id")})
    
    guild = get_guild(int(transcript_doc.get("guild_id")))
    guild_name = guild['name'] if guild else "Unknown Server"

    messages = transcript_doc.get("messages", [])
        
    return render_template(
        "tickets/transcript.html", 
        transcript=transcript_doc, 
        ticket=ticket, 
        messages=messages, 
        guild_name=guild_name,
        guild=guild
    )

@ticket_module.route('/transcripts/<guild_id>', methods=['GET'])
@login_required
def view_guild_transcripts(guild_id):
    guild_id = int(guild_id)
    guild = get_guild(guild_id)
    if not guild:
        flash("Guild not found or you do not have access to it.", "error")
        return redirect(url_for("dashboard"))
    
    member = get_guild_member(guild_id, session["user_id"])
    if not member:
        flash("You do not have access to this guild.", "error")
        return redirect(url_for("dashboard"))
    
    has_permission = False

    has_perm = check_permissions(guild_id, session["user_id"])
    if has_perm:
        has_permission = True

    if not has_permission:
        flash("You don't have permission to view transcripts of this guild", "danger")
        return redirect(url_for('dashboard'))
    
    transcripts = list(mongo_db["ticket_transcripts"].find({"guild_id": guild_id}).sort("created_at", -1))
    
    return render_template("tickets/view_transcripts.html", guild=guild, transcripts=transcripts)