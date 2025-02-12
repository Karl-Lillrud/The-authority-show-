# app.py
from flask import Flask, render_template, request, jsonify, url_for, session, redirect, g
from azure.cosmos import CosmosClient, PartitionKey
from register import register_bp
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import random
import smtplib
import venvupdate
from email.mime.text import MIMEText

# Update virtual environment and requirements
venvupdate.update_venv_and_requirements()
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv("SECRET_KEY")
app.config['PREFERRED URL SCHEME'] = 'https'
app.register_blueprint(register_bp)

APP_ENV = os.getenv("APP_ENV", "production")

# Cosmos DB Configuration
COSMOSDB_URI = os.getenv("COSMOS_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOS_KEY")
DATABASE_ID = "podmanagedb"

if not COSMOSDB_URI or not COSMOSDB_KEY:
    raise ValueError("Cosmos DB credentials are missing.")

client = CosmosClient(COSMOSDB_URI, COSMOSDB_KEY)
database = client.get_database_client(DATABASE_ID)

# Create containers if they don't exist
users_container = database.create_container_if_not_exists(
    id="users",
    partition_key=PartitionKey(path="/email"),
    offer_throughput=400
)
bookings_container = database.create_container_if_not_exists(
    id="bookings",
    partition_key=PartitionKey(path="/email"),
    offer_throughput=400
)
newsletter_container = database.create_container_if_not_exists(
    id="newsletter",
    partition_key=PartitionKey(path="/email"),
    offer_throughput=400
)
podcasts_container = database.create_container_if_not_exists(
    id="podcasts",
    partition_key=PartitionKey(path="/creator_id"),
    offer_throughput=400
)

PI_BASE_URL = "http://127.0.0.1:8000" if APP_ENV == "local" else "https://app.podmanager.ai"

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

@app.before_request
def load_user():
    g.user_id = session.get("user_id")

# ----------------- User Endpoints (using "users" container) -----------------

@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgotpassword/forgot-password.html')
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415  
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400
    email = data.get("email", "").strip().lower()
    print(f"🔍 Checking for email: {email}")
    query = "SELECT * FROM c WHERE LOWER(c.email) = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(users_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
    if not users:
        return jsonify({"error": "No account found with that email"}), 404
    reset_code = str(random.randint(100000, 999999))
    user = users[0]
    user["reset_code"] = reset_code
    users_container.upsert_item(user)
    try:
        send_reset_email(email, reset_code)
        return jsonify({"message": "Reset code sent successfully.", "redirect_url": url_for('enter_code')}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

@app.route('/enter-code', methods=['GET', 'POST'])
def enter_code():
    print(f"🔍 Request Headers: {request.headers}")
    print(f"🔍 Request Data: {request.data}")
    if request.method == 'GET':
        return render_template('forgotpassword/enter-code.html')
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON format"}), 400
    email = data.get("email", "").strip().lower()
    entered_code = data.get("code", "").strip()
    print(f"🔍 Checking Email: {email}, Code: {entered_code}")
    query = "SELECT * FROM c WHERE LOWER(c.email) = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(users_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
    if not users or users[0].get("reset_code") != entered_code:
        return jsonify({"error": "Invalid or expired reset code."}), 400
    print("✅ Code Verified, Redirecting to Reset Password")
    return jsonify({"message": "Code is Valid.", "redirect_url": url_for('reset_password')}), 200

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        return render_template('forgotpassword/reset-password.html')
    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    new_password = data.get("password", "")
    query = "SELECT * FROM c WHERE LOWER(c.email) = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(users_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
    if not users:
        return jsonify({"error": "User not found."}), 404
    user = users[0]
    user["passwordHash"] = generate_password_hash(new_password)
    user.pop("reset_code", None)
    users_container.upsert_item(user)
    return jsonify({"message": "Password updated successfully.", "redirect_url": url_for('signin')}), 200

def send_reset_email(email, reset_code):
    try:
        msg = MIMEText(f"Your password reset code is: {reset_code}\nUse this code to reset your password.")
        msg["Subject"] = "Password Reset Request"
        msg["From"] = EMAIL_USER
        msg["To"] = email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, email, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
        raise

@app.route('/resend-code', methods=['POST'])
def resend_code():
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415  
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    print(f"🔍 Resending code for email: {email}")
    query = "SELECT * FROM c WHERE LOWER(c.email) = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(users_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
    if not users:
        return jsonify({"error": "No account found with that email"}), 404
    reset_code = str(random.randint(100000, 999999))
    user = users[0]
    user["reset_code"] = reset_code
    users_container.upsert_item(user)
    try:
        send_reset_email(email, reset_code)
        return jsonify({"message": "New reset code sent successfully."}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to resend code: {str(e)}"}), 500

@app.route('/', methods=['GET'])
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return render_template('signin.html')
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    query = "SELECT * FROM c WHERE LOWER(c.email) = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(users_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
    if not users or not check_password_hash(users[0]["passwordHash"], password):
        return jsonify({"error": "Invalid email or password"}), 401
    session["user_id"] = str(users[0]["id"])
    session["email"] = users[0]["email"]
    session.permanent = True
    return jsonify({"message": "Login successful", "redirect_url": "/dashboard"}), 200

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('dashboard/dashboard.html')

@app.route('/homepage', methods=['GET'])
def homepage():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('dashboard/homepage.html')

@app.route('/accountsettings', methods=['GET'])
def accountsettings():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('dashboard/accountsettings.html')

# ----------------- Podcast Endpoints (using "podcasts" container) -----------------

@app.route('/podcastmanagement', methods=['GET'])
def podcastmanagement():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('dashboard/podcastmanagement.html')

@app.route('/podprofile', methods=['GET','POST'])
def podprofile():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('podprofile/index.html')

@app.route('/get_user_podcasts', methods=['GET'])
def get_user_podcasts():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    query = "SELECT * FROM c WHERE c.creator_id = @user_id"
    parameters = [{"name": "@user_id", "value": g.user_id}]
    podcasts = list(podcasts_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
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
        podcasts_container.upsert_item(podcast_item)
        return jsonify({"message": "Podcast registered successfully", "redirect_url": "/production-team"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to register podcast: {str(e)}"}), 500

@app.route('/taskmanagement', methods=['GET'])
def taskmanagement():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('dashboard/taskmanagement.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
