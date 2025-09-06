from flask import render_template, redirect, url_for, request, flash, Blueprint, session
from flask_login import login_required, current_user
from cyni import bot
from dotenv import load_dotenv
from Database.Mongo import mongo_db
from utils.site_utils import check_permissions, get_guild, get_guild_member, get_guild_channels, get_guild_roles

load_dotenv()

welcome_route = Blueprint('welcome_module', __name__)

@welcome_route.route('/dashboard/<guild_id>/settings/welcome', methods=['GET', 'POST'])
@login_required
def welcome(guild_id):
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
    
    guild_data = mongo_db["settings"].find_one({"_id": guild['id']})
    if request.method == 'POST':
        welcome_message = request.form.get('welcome_message', '')
        welcome_channel = request.form.get('welcome_channel', '')
        welcome_role = request.form.get('welcome_role', '')
        use_embed = request.form.get('use_embed', '')
        embed_color = request.form.get('embed_color_text', '')
        embed_title = request.form.get('embed_title', '')
        enable_welcome = request.form.get('enabled', '')

        welcome_module = guild_data.get('welcome_module', {})
        welcome_module.get('welcome_message', " ")
        welcome_module.get('welcome_channel', 0)
        welcome_module.get('welcome_role', 0)
        welcome_module.get('embed_color', " ")
        welcome_module.get('embed_title', " ")
        welcome_module.get('use_embed', False)
        welcome_module.get('enabled', False)
        
        welcome_module['welcome_message'] = welcome_message
        welcome_module['welcome_channel'] = int(welcome_channel)
        welcome_module['welcome_role'] = int(welcome_role)
        welcome_module['use_embed'] = True if use_embed == 'on' else False
        welcome_module['embed_color'] = embed_color
        welcome_module['embed_title'] = embed_title
        welcome_module['enabled'] = True if enable_welcome == 'on' else False

        mongo_db["settings"].update_one({"_id": guild.id}, {"$set": {"welcome_module": welcome_module}})
        return redirect(url_for('welcome_module.welcome', guild_id=guild.id))

    channels = get_guild_channels(guild['id'])
    roles = get_guild_roles(guild['id'])
    return render_template('welcome_module/index.html', user=current_user, guild=guild, guild_data=guild_data, channels=channels, roles=roles)