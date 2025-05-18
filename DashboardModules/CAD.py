from flask import render_template, redirect, url_for, request, flash, Blueprint
from flask_login import login_required, current_user
from cyni import bot

cad_route = Blueprint('cad', __name__)

@cad_route.route('/cad/<guild_id>', methods=['GET', 'POST'])
@login_required
def welcome(guild_id):
    if request.method == 'POST':
        if request.form.get('start'):
            bot.start_cad(guild_id)
            flash('CAD started successfully!', 'success')
        elif request.form.get('stop'):
            bot.stop_cad(guild_id)
            flash('CAD stopped successfully!', 'success')
        else:
            flash('Invalid action!', 'danger')
        return redirect(url_for('cad.welcome', guild_id=guild_id))
    elif request.method == 'GET':
        guild = bot.get_guild(int(guild_id))
        if guild is None:
            flash('Guild not found!', 'danger')
            return redirect(url_for('cad.welcome', guild_id=guild_id))
        return render_template('cad/main.html', user=current_user, guild=guild)