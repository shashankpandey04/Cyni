from flask import render_template, redirect, url_for, request, flash, Blueprint, session
from flask_login import login_required, current_user
from cyni import bot
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client["cyni"] if os.getenv("PRODUCTION_TOKEN") else mongo_client["dev"]

loa_route = Blueprint('loa_module', __name__)