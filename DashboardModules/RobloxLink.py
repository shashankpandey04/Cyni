from flask import render_template, redirect, url_for, request, flash, Blueprint
from flask_login import login_required, current_user
import os
from dotenv import load_dotenv
from Database.Mongo import mongo_db
import requests
from jose import jwt

load_dotenv()

ROBLOX_CLIENT_ID = os.getenv("ROBLOX_CLIENT_ID")
ROBLOX_CLIENT_SECRET = os.getenv("ROBLOX_CLIENT_SECRET")
ROBLOX_REDIRECT_URI = os.getenv("ROBLOX_REDIRECT_URI")
ROBLOX_TOKEN_URL = "https://apis.roblox.com/oauth/v1/token"
ROBLOX_AUTH_URL = "https://apis.roblox.com/oauth/v1/authorize"

roblox_link_route = Blueprint(
    'roblox_link',
    __name__,
    url_prefix="/api/verify/roblox/v1"
)


@roblox_link_route.route('/link', methods=['GET'])
@login_required
def roblox_link():
    user_id = current_user.id
    import secrets
    state = secrets.token_urlsafe(16)
    mongo_db.pending_roblox_oauth.update_one(
        {"user_id": user_id},
        {"$set": {"state": state}},
        upsert=True
    )

    oauth_url = (
        f"{ROBLOX_AUTH_URL}"
        f"?client_id={ROBLOX_CLIENT_ID}"
        f"&redirect_uri={ROBLOX_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20profile"
        f"&state={state}"
    )
    return redirect(oauth_url)

@roblox_link_route.route('/response', methods=['GET'])
@login_required
def roblox_response():
    user_id = current_user.id
    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state:
        flash("Missing code or state", "danger")
        return redirect(url_for("dashboard.index"))

    db_state = mongo_db.pending_roblox_oauth.find_one({"user_id": user_id})
    if not db_state or db_state.get("state") != state:
        flash("Invalid or expired state", "danger")
        return redirect(url_for("dashboard.index"))

    data = {
        "client_id": ROBLOX_CLIENT_ID,
        "client_secret": ROBLOX_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": ROBLOX_REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_resp = requests.post(ROBLOX_TOKEN_URL, data=data, headers=headers)
    token_data = token_resp.json()

    id_token = token_data.get("id_token")
    if not id_token:
        flash("Failed to fetch Roblox account info", "danger")
        return redirect(url_for("dashboard.index"))

    profile = jwt.get_unverified_claims(id_token)
    roblox_info = {
        "roblox_user_id": int(profile.get("sub")),
        "username": profile.get("preferred_username"),
        "displayName": profile.get("name"),
        "avatar": profile.get("picture"),
    }

    mongo_db.roblox_oauth.update_one(
        {"discord_user_id": int(user_id)},
        {"$set": roblox_info},
        upsert=True
    )

    mongo_db.pending_roblox_oauth.delete_one({"user_id": user_id})

    return render_template("roblox/linked.html")
