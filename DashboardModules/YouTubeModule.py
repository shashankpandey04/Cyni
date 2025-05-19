from flask import render_template, redirect, url_for, request, flash, Blueprint, session, jsonify
from flask_login import login_required, current_user
from cyni import bot
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import datetime
import re

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client["cyni"] if os.getenv("PRODUCTION_TOKEN") else mongo_client["dev"]
bot_token = os.getenv("PRODUCTION_TOKEN") if os.getenv("PRODUCTION_TOKEN") else os.getenv("DEV_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube_module = Blueprint('youtube_module', __name__)

@youtube_module.route('/dashboard/<guild_id>/settings/youtube', methods=['GET', 'POST'])
@login_required
def youtube_settings(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
        
    youtube_config = mongo_db["youtube_config"].find_one({"guild_id": guild_id}) or {"channels": []}
    
    channels = {channel.id: channel.name for channel in guild.text_channels}
    
    return render_template("youtube/main.html", 
                           guild=guild,
                           youtube_config=youtube_config,
                           channels=channels)

@youtube_module.route('/dashboard/<guild_id>/settings/youtube/add', methods=['POST'])
@login_required
def add_youtube_channel(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    
    youtube_url = request.form.get('youtube_url')
    discord_channel_id = int(request.form.get('discord_channel_id'))
    message_format = request.form.get('message_format', "{everyone} New video from **{channel_name}**!\n{video_url}")
    
    youtube_id = extract_channel_id(youtube_url)
    if not youtube_id:
        flash("Invalid YouTube channel URL", "danger")
        return redirect(url_for('youtube_module.youtube_settings', guild_id=guild_id))
    
    youtube_api = build_youtube_api()
    channel_response = youtube_api.channels().list(
        part="snippet",
        id=youtube_id
    ).execute()
    
    if not channel_response["items"]:
        flash("YouTube channel not found", "danger")
        return redirect(url_for('youtube_module.youtube_settings', guild_id=guild_id))
    
    channel_title = channel_response["items"][0]["snippet"]["title"]
    
    config = mongo_db["youtube_config"].find_one({"guild_id": guild_id})
    if not config:
        mongo_db["youtube_config"].insert_one({
            "guild_id": guild_id,
            "channels": [{
                "youtube_id": youtube_id,
                "channel_name": channel_title,
                "discord_channel_id": discord_channel_id,
                "last_video_id": "",
                "message_format": message_format,
                "last_check": datetime.datetime.now().timestamp()
            }]
        })
    else:
        for channel in config.get("channels", []):
            if channel["youtube_id"] == youtube_id and channel["discord_channel_id"] == discord_channel_id:
                flash("This YouTube channel is already being tracked in the specified Discord channel", "warning")
                return redirect(url_for('youtube_module.youtube_settings', guild_id=guild_id))
        
        mongo_db["youtube_config"].update_one(
            {"guild_id": guild_id},
            {"$push": {"channels": {
                "youtube_id": youtube_id,
                "channel_name": channel_title,
                "discord_channel_id": discord_channel_id,
                "last_video_id": "",
                "message_format": message_format,
                "last_check": datetime.datetime.now().timestamp()
            }}}
        )
    
    flash(f"YouTube channel '{channel_title}' added successfully", "success")
    return redirect(url_for('youtube_module.youtube_settings', guild_id=guild_id))

@youtube_module.route('/dashboard/<guild_id>/settings/youtube/remove', methods=['POST'])
@login_required
def remove_youtube_channel(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    
    youtube_id = request.form.get('youtube_id')
    discord_channel_id = int(request.form.get('discord_channel_id'))
    
    result = mongo_db["youtube_config"].update_one(
        {"guild_id": guild_id},
        {"$pull": {"channels": {"youtube_id": youtube_id, "discord_channel_id": discord_channel_id}}}
    )
    
    if result.modified_count > 0:
        flash("YouTube channel removed successfully", "success")
    else:
        flash("Failed to remove YouTube channel", "danger")
    
    return redirect(url_for('youtube_module.youtube_settings', guild_id=guild_id))

@youtube_module.route('/dashboard/<guild_id>/settings/youtube/edit', methods=['POST'])
@login_required
def edit_youtube_channel(guild_id):
    guild_id = int(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild:
        flash('Guild not found', 'danger')
        return redirect(url_for('dashboard'))
        
    member = guild.get_member(int(session["user_id"]))
    if not member or not (member.guild_permissions.manage_guild or member.guild_permissions.administrator):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for('dashboard'))
    
    youtube_id = request.form.get('youtube_id')
    discord_channel_id = int(request.form.get('discord_channel_id'))
    message_format = request.form.get('message_format')

    result = mongo_db["youtube_config"].update_one(
        {"guild_id": guild_id, "channels.youtube_id": youtube_id, "channels.discord_channel_id": discord_channel_id},
        {"$set": {"channels.$.message_format": message_format}}
    )
    
    if result.modified_count > 0:
        flash("YouTube notification settings updated successfully", "success")
    else:
        flash("Failed to update YouTube notification settings", "danger")
    
    return redirect(url_for('youtube_module.youtube_settings', guild_id=guild_id))

def extract_channel_id(url_or_id):
    """Extract YouTube channel ID from a URL or return the ID if it's already a valid ID"""
    if re.match(r'^[A-Za-z0-9_-]{24}$', url_or_id):
        return url_or_id

    channel_url_pattern = r'youtube\.com\/channel\/([A-Za-z0-9_-]+)'
    match = re.search(channel_url_pattern, url_or_id)
    if match:
        return match.group(1)
    
    username_patterns = [
        r'youtube\.com\/c\/([A-Za-z0-9_-]+)',
        r'youtube\.com\/user\/([A-Za-z0-9_-]+)',
        r'youtube\.com\/@([A-Za-z0-9_-]+)'
    ]
    
    for pattern in username_patterns:
        match = re.search(pattern, url_or_id)
        if match:
            username = match.group(1)
            try:
                youtube_api = build_youtube_api()
                response = youtube_api.search().list(
                    part="snippet",
                    q=username,
                    type="channel",
                    maxResults=1
                ).execute()
                
                if response["items"]:
                    return response["items"][0]["snippet"]["channelId"]
            except:
                pass
    
    return None

def build_youtube_api():
    """Build the YouTube API client"""
    import googleapiclient.discovery
    return googleapiclient.discovery.build(
        "youtube", "v3", developerKey=YOUTUBE_API_KEY
    )
