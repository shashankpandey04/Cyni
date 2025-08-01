from flask import render_template, redirect, url_for, request, flash, Blueprint, session, jsonify
from flask_login import login_required, current_user
from cyni import bot
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import datetime
import json
import uuid
import requests
from Database.Mongo import mongo_db

load_dotenv()

bot_token = os.getenv("PRODUCTION_TOKEN") if os.getenv("PRODUCTION_TOKEN") else os.getenv("DEV_TOKEN")

partnership_module = Blueprint('partnership_module', __name__)

@partnership_module.route('/partnership', methods=['GET', 'POST'])
@login_required
async def partnership_dashboard():
    if request.method == 'POST':
        # Handle form submission
        pass
    return render_template('partnership.html', user=current_user)

@partnership_module.route('/partnership/create', methods=['POST'])
@login_required
async def create_partnership():
    data = request.json
    # Validate and process the data
    return jsonify({"message": "Partnership created successfully!"}), 201

@partnership_module.route('/partnership/list', methods=['GET'])
@login_required
async def list_partnerships():
    partnerships = mongo_db.partnerships.find({"user_id": current_user.id})
    return render_template('partnership_list.html', user=current_user, partnerships=partnerships)

@partnership_module.route('/partnership/delete/<partnership_id>', methods=['POST'])
@login_required
async def delete_partnership(partnership_id):
    mongo_db.partnerships.delete_one({"_id": partnership_id, "user_id": current_user.id})
    return jsonify({"message": "Partnership deleted successfully!"}), 200

@partnership_module.route('/partnership/details/<partnership_id>', methods=['GET'])
@login_required
async def partnership_details(partnership_id):
    partnership = mongo_db.partnerships.find_one({"_id": partnership_id, "user_id": current_user.id})
    if not partnership:
        return jsonify({"message": "Partnership not found!"}), 404
    return render_template('partnership_details.html', user=current_user, partnership=partnership)


@partnership_module.route('/partnership/update/<partnership_id>', methods=['POST'])
@login_required
async def update_partnership(partnership_id):
    data = request.json
    # Validate and process the data
    return jsonify({"message": "Partnership updated successfully!"}), 200
