from flask import Flask, render_template, request, jsonify, url_for, session, redirect, g, Blueprint
from azure.cosmos import CosmosClient
from routes.register import register_bp
from routes.forgot_pass import forgotpass_bp
from routes.signin import signin_bp
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import random
import smtplib
import utils.venvupdate as venvupdate
from email.mime.text import MIMEText
from database.cosmos_connection import container
from utils import venvupdate

# update the virtual environment and requirements
venvupdate.update_venv_and_requirements()

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv("SECRET_KEY")
app.config['PREFERRED URL SCHEME'] = 'https'
app.register_blueprint(register_bp)
app.register_blueprint(forgotpass_bp)
app.register_blueprint(signin_bp)

APP_ENV = os.getenv("APP_ENV", "production")  # Default to production

PI_BASE_URL = "http://127.0.0.1:8000" if APP_ENV == "local" else "https://app.podmanager.ai"

@app.before_request
def load_user():
    g.user_id = session.get("user_id")

# 📌 Dashboard
@app.route('/dashboard', methods=['GET'],) #BP ROUTE?
def dashboard():
    if not g.user_id:
        return redirect(signin_bp)
    return render_template('dashboard/dashboard.html')

# ✅ Serves the homepage page
@app.route('/homepage', methods=['GET'])
def homepage():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('dashboard/homepage.html')

# ✅ Serves the settings page
@app.route('/accountsettings', methods=['GET'])
def accountsettings():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('dashboard/accountsettings.html')

# ✅ Serves the profile page
@app.route('/podcastmanagement', methods=['GET'])
def podcastmanagement():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('dashboard/podcastmanagement.html')

# ✅ Serves the tasks page
@app.route('/taskmanagement', methods=['GET'])
def taskmanagement():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('dashboard/taskmanagement.html')

@app.route('/podprofile', methods=['GET','POST'])
def podprofile():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('podprofile/index.html')

@app.route('/team', methods=['GET','POST'])
def team():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('team/index.html')

@app.route('/guest', methods=['GET','POST'])
def guest():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('guest/index.html')

@app.route('/profile/<guest_id>', methods=['GET'])
def guest_profile(guest_id):
    # Replace this with your actual data retrieval logic,
    # for example, querying your database or another data source.
    guests = load_all_guests()  # This should return a list/dictionary of guest info.
    guest = next((g for g in guests if g["id"] == guest_id), None)
    if guest is None:
        return "Guest not found", 404
    return render_template('guest/profile.html', guest=guest)



@app.route('/settings', methods=['GET','POST'])
def settings():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('settings/index.html')

@app.route('/get_user_podcasts', methods=['GET'])
def get_user_podcasts():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    query = "SELECT * FROM c WHERE c.creator_id = @user_id"
    parameters = [{"name": "@user_id", "value": g.user_id}]
    podcasts = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
    return jsonify(podcasts)

@app.route('/register_podcast', methods=['POST'])
def register_podcast():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    pod_name = data.get("podName", "").strip()
    pod_rss = data.get("podRss", "").strip()

    if not pod_name or not pod_rss:
        return jsonify({"error": "Podcast Name and RSS URL are required"}), 400

    podcast_item = {
        "id": str(random.randint(100000, 999999)),
        "creator_id": g.user_id,
        "podName": pod_name,
        "podRss": pod_rss,
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        container.upsert_item(podcast_item)
        return jsonify({"message": "Podcast registered successfully", "redirect_url": "/production-team"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to register podcast: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
