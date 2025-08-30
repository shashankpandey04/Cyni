from flask import render_template, redirect, url_for, request, flash, Blueprint, session
from flask_login import login_required, current_user
from dotenv import load_dotenv
from Database.Mongo import mongo_db
from utils.site_utils import check_permissions, get_guild, get_guild_member
from datetime import datetime

load_dotenv()

spreadsheet_route = Blueprint(
    'cyni_spreadsheet',
    __name__,
)

def format_duration(seconds: int) -> str:
    """Format seconds into Hh Mm Ss string"""
    if seconds <= 0:
        return "N/A"
    hours, remainder = divmod(seconds, 3600)
    minutes, sec = divmod(remainder, 60)
    return f"{hours}h {minutes}m {sec}s"

@spreadsheet_route.route('/spreadsheet/shifts/<guild_id>/<shift_type>', methods=['GET'])
@login_required
def shift_spreadsheet(guild_id, shift_type):
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

    try:
        # Aggregate leaderboard
        leaderboard_data = list(mongo_db["shift_logs"].aggregate([
            {
            "$match": {
                "guild_id": int(guild_id),
                "end_epoch": {"$ne": 0},
                "type": shift_type.lower()
            }
            },
            {
            "$group": {
                "_id": "$user_id",
                "total_duration": {"$sum": "$duration"},
                "username": {"$first": "$username"}  # Include the username
            }
            },
            {
            "$sort": {"total_duration": -1}
            }
        ]))

        # Format for template
        for entry in leaderboard_data:
            entry["formatted_duration"] = format_duration(entry["total_duration"])

    except Exception as e:
        print(f"Error fetching leaderboard data: {e}")
        leaderboard_data = []

    return render_template(
        'spreadsheets/shift.html',
        leaderboard_data=leaderboard_data,
        user=current_user,
        guild=guild,
        shift_type=shift_type.capitalize()
    )
