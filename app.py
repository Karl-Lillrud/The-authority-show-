# app.py
import os, random, smtplib, venvupdate, urllib.parse
from flask import Flask, render_template, request, jsonify, url_for, session, redirect, g
from azure.cosmos import CosmosClient, PartitionKey
from google_auth_oauthlib.flow import Flow
from register import register_bp
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
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
    # Load user information from session into g
    g.user_id = session.get("user_id")
    g.email = session.get("email")  

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
    query = "SELECT * FROM c WHERE LOWER(c.email) = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(users_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
    if not users or users[0].get("reset_code") != entered_code:
        return jsonify({"error": "Invalid or expired reset code."}), 400
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

# ----------------- Sign-in and Redirect Based on Pod Profile Completion -----------------

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
    user_doc = users[0]
    session["user_id"] = str(user_doc["id"])
    session["email"] = user_doc["email"]
    session.permanent = True
    # Redirect first-time users to podprofile; others to dashboard.
    redirect_url = "/podprofile" if not user_doc.get("podprofile_completed") else "/dashboard"
    return jsonify({"message": "Login successful", "redirect_url": redirect_url}), 200

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

@app.route('/accountsettings', methods=['GET', 'POST'])
def accountsettings():
    if not g.user_id:
        return redirect(url_for('signin'))
    if request.method == 'GET':
        # Load current user profile from the "users" container
        current_email = session.get("email").lower()
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters = [{"name": "@email", "value": current_email}]
        users = list(users_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        user_doc = users[0] if users else {}
        return render_template('dashboard/accountsettings.html', user=user_doc)
    else:
        # Handle profile update submission
        # Accept either JSON or form data:
        if request.content_type == "application/json":
            data = request.get_json()
        else:
            data = request.form

        # Expected fields (update your HTML form to use these names/IDs)
        # For example, use: name="full-name", name="email", name="current-password",
        # name="new-password", name="confirm-password".
        full_name       = data.get("full-name", "").strip()
        # NOTE: Updating email is not recommended if email is used as the partition key.
        # new_email      = data.get("email", "").strip().lower()
        current_password= data.get("current-password", "")
        new_password    = data.get("new-password", "")
        confirm_password= data.get("confirm-password", "")

        if new_password and new_password != confirm_password:
            return jsonify({"error": "New password and confirmation do not match."}), 400

        # Retrieve the current user document from the database using session email.
        current_email = session.get("email").lower()
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters = [{"name": "@email", "value": current_email}]
        users = list(users_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        if not users:
            return jsonify({"error": "User not found."}), 404

        user_doc = users[0]

        # If the user wants to change their password, verify the current password.
        if new_password:
            if not current_password:
                return jsonify({"error": "Current password is required to change password."}), 400
            if not check_password_hash(user_doc.get("passwordHash", ""), current_password):
                return jsonify({"error": "Current password is incorrect."}), 401
            user_doc["passwordHash"] = generate_password_hash(new_password)

        # Update the full name if provided.
        if full_name:
            user_doc["fullName"] = full_name

        # (Optional) If you want to update other fields (e.g. profile picture URL), do so here.

        try:
            users_container.upsert_item(user_doc)
            return jsonify({"message": "Profile updated successfully.", "redirect_url": "/dashboard"}), 200
        except Exception as e:
            return jsonify({"error": f"Failed to update profile: {str(e)}"}), 500

# ----------------- Podcast Endpoints -----------------

@app.route('/podcastmanagement', methods=['GET'])
def podcastmanagement():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('dashboard/podcastmanagement.html')

# Modified Pod Profile Endpoint to Handle GET and POST
@app.route('/podprofile', methods=['GET', 'POST'])
def podprofile():
    if not g.user_id:
        return redirect(url_for('signin'))
    if request.method == 'GET':
        return render_template('podprofile/index.html')
    # Expect JSON data from the podprofile form submission
    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    data = request.get_json()
    # Extract fields from the submitted data
    pod_name      = data.get("podName", "").strip()
    pod_rss       = data.get("podRss", "").strip()
    pod_logo      = data.get("podLogo", "").strip()
    host_name     = data.get("hostName", "").strip()
    calendar_url  = data.get("calendarUrl", "").strip()
    guest_form    = data.get("guestForm", "").strip()
    facebook      = data.get("facebook", "").strip()
    instagram     = data.get("instagram", "").strip()
    linkedin      = data.get("linkedin", "").strip()
    twitter       = data.get("twitter", "").strip()
    tiktok        = data.get("tiktok", "").strip()
    pinterest     = data.get("pinterest", "").strip()
    website       = data.get("website", "").strip()
    podcast_email = data.get("email", "").strip()
    production_team = data.get("productionTeam", [])  # Expect a list of team member objects

    # Validate required fields (customize as needed)
    if not pod_name or not pod_rss or not host_name or not podcast_email:
        return jsonify({"error": "Missing required fields"}), 400

    podcast_profile = {
        "id": str(random.randint(100000, 999999)),
        "creator_id": g.user_id,
        "podName": pod_name,
        "podRss": pod_rss,
        "podLogo": pod_logo,
        "hostName": host_name,
        "calendarUrl": calendar_url,
        "guestForm": guest_form,
        "facebook": facebook,
        "instagram": instagram,
        "linkedin": linkedin,
        "twitter": twitter,
        "tiktok": tiktok,
        "pinterest": pinterest,
        "website": website,
        "email": podcast_email,
        "productionTeam": production_team,
        "created_at": datetime.utcnow().isoformat()
    }
    try:
        podcasts_container.upsert_item(podcast_profile)
    except Exception as e:
        return jsonify({"error": f"Failed to save podcast profile: {str(e)}"}), 500

    # Update user document to mark pod profile as completed
    try:
        query = "SELECT * FROM c WHERE LOWER(c.email) = @email"
        parameters = [{"name": "@email", "value": session["email"].lower()}]
        user_docs = list(users_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        if user_docs:
            user_doc = user_docs[0]
            user_doc["podprofile_completed"] = True
            users_container.upsert_item(user_doc)
    except Exception as e:
        return jsonify({"error": f"Failed to update user profile: {str(e)}"}), 500

    return jsonify({"message": "Podcast profile submitted successfully.", "redirect_url": "/dashboard"}), 200

@app.route('/calendar_connect')
def calendar_connect():
    # Use g to get the current user's email.
    user_email = g.email
    if not user_email:
        return jsonify({"error": "User email not available."}), 400

    # Derive the calendar provider based on the email domain.
    domain = user_email.split("@")[-1].lower()
    if domain in ["gmail.com", "googlemail.com"]:
        provider = "google"
    elif domain in ["outlook.com", "hotmail.com", "live.com"]:
        provider = "outlook"
    elif domain in ["yahoo.com"]:
        provider = "yahoo"
    else:
        # Fallback: default to Google if domain is unknown.
        provider = "google"

    # Build the authorization URL for the chosen provider.
    if provider == "google":
        # Replace with your registered Google OAuth client ID.
        client_id = "284426805702-be7g0vc6gs54f9tf3iop00v7mpklqjpb.apps.googleusercontent.com"
        redirect_uri = url_for('google_calendar_callback', _external=True)
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/calendar",
            "access_type": "offline",
            "include_granted_scopes": "true"
        }
        auth_url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)
        return redirect(auth_url)

    elif provider == "outlook":
        # Replace with your registered Outlook OAuth client ID.
        client_id = "YOUR_OUTLOOK_CLIENT_ID"
        redirect_uri = url_for('outlook_calendar_callback', _external=True)
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "Calendars.Read offline_access",
            "response_mode": "query"
        }
        auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?" + urllib.parse.urlencode(params)
        return redirect(auth_url)

    elif provider == "yahoo":
        # Replace with your registered Yahoo OAuth client ID.
        client_id = "YOUR_YAHOO_CLIENT_ID"
        redirect_uri = url_for('yahoo_calendar_callback', _external=True)
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "language": "en-us",
            "scope": "sdct-w"  # Adjust the scope as needed.
        }
        auth_url = "https://api.login.yahoo.com/oauth2/request_auth?" + urllib.parse.urlencode(params)
        return redirect(auth_url)

    else:
        return jsonify({"error": "Unsupported provider."}), 400

@app.route('/google_calendar_callback')
def google_calendar_callback():
    # For demonstration, simply return the code.
    code = request.args.get("code")
    return "Google Calendar callback received code: " + str(code)

@app.route('/outlook_calendar_callback')
def outlook_calendar_callback():
    code = request.args.get("code")
    return "Outlook Calendar callback received code: " + str(code)

@app.route('/yahoo_calendar_callback')
def yahoo_calendar_callback():
    code = request.args.get("code")
    return "Yahoo Calendar callback received code: " + str(code)
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
        return jsonify({"message": "Podcast registered successfully", "redirect_url": "/podprofile"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to register podcast: {str(e)}"}), 500
    
@app.route('/send_invite', methods=['POST'])
def send_invite():
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    data = request.get_json()
    # Ensure all required fields are provided.
    from_email = data.get("from")
    to_email = data.get("to")
    subject = data.get("subject")
    body = data.get("body")
    if not (from_email and to_email and subject and body):
        return jsonify({"error": "Missing required email parameters."}), 400

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(from_email, to_email, msg.as_string())

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/taskmanagement', methods=['GET'])
def taskmanagement():
    if not g.user_id:
        return redirect(url_for('signin'))
    return render_template('dashboard/taskmanagement.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
