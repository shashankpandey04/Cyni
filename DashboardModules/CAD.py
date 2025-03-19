from flask import render_template, redirect, url_for, request, flash, Blueprint
from flask_login import login_required, current_user


cad_route = Blueprint('cad', __name__)

@cad_route.route('/cad/<guild_id>', methods=['GET', 'POST'])
@login_required
def welcome():
    return render_template('dashboard/cad.html', user=current_user)