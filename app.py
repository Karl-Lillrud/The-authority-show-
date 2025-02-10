from flask import Flask, render_template, request, jsonify, url_for, session, redirect
from azure.cosmos import CosmosClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
import smtplib
from email.mime.text import MIMEText
from register import register_bp

# Load environment variables
load_dotenv()

# Flask Setup
app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"  # Store session data
app.config["SESSION_PERMANENT"] = False
app.register_blueprint(register_bp)
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Determine environment (local or production)
APP_ENV = os.getenv("APP_ENV", "production")  # Default to production

# CosmosDB Configuration
COSMOSDB_URI = os.getenv("COSMOS_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOS_KEY")
DATABASE_ID = "podmanagedb"
CONTAINER_ID = "users"

if not COSMOSDB_URI or not COSMOSDB_KEY:
    raise ValueError("Cosmos DB credentials are missing.")

# Initialize Cosmos Client
client = CosmosClient(COSMOSDB_URI, COSMOSDB_KEY)
database = client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Determine API base URL based on environment
API_BASE_URL = "http://127.0.0.1:8000" if APP_ENV == "local" else "https://app.podmanager.ai"

@app.route('/forgotpassword', methods=['GET','POST'])
def forgot_password():
    if request.content_type != 'application/json':
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415  # Unsupported Media Type

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    email = data.get("email", "").strip().lower()

    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

    if not users:
        return jsonify({"error": "No account found with that email"}), 404

    reset_code = str(random.randint(100000, 999999))

    user = users[0]
    user["reset_code"] = reset_code
    container.upsert_item(user)  # Store the reset code

    try:
        send_reset_email(email, reset_code)
        return jsonify({"message": "Reset code sent successfully.", "redirect_url": url_for('enter_code')}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/enter-code', methods=['GET','POST'])
def enter_code():
    if request.method == 'GET':
        return render_template('forgotpassword/enter-code.html')# ✅ Allow GET to load the page
 
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
 
    try:
        data = request.get_json(force=True)  # ✅ Ensure JSON format
    except Exception:
        return jsonify({"error": "Invalid JSON format"}), 400
 
    email = data.get("email", "").strip().lower()
    entered_code = data.get("code", "").strip()
 
    query = "SELECT * FROM c WHERE LOWER(c.email) = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
 
    if not users or users[0].get("reset_code") != entered_code:
        return jsonify({"error": "Invalid or expired reset code."}), 400
 
    return jsonify({
        "message": "Code verified. Redirecting...",
        "redirect_url": "/reset-password?email=" + email
    }), 200

@app.route('/reset-password', methods=['GET','POST'])
def reset_password():
    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
 
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    new_password = data.get("password", "")
 
    query = "SELECT * FROM c WHERE LOWER(c.email) = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
 
    if not users:
        return jsonify({"error": "User not found."}), 404
 
    user = users[0]
    user["passwordHash"] = generate_password_hash(new_password)
    user.pop("reset_code", None)  # Remove reset code
    container.upsert_item(user)
 
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


@app.route('/', methods=['GET'])
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    try:
        if request.method == 'GET':
            return render_template('signin.html', api_base_url=API_BASE_URL)

        data = request.get_json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        # Query CosmosDB
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters = [{"name": "@email", "value": email}]
        users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if not users:
            return jsonify({"error": "Invalid email or password"}), 401

        # Password comparison
        stored_hash = users[0].get("passwordHash", "")
        if not check_password_hash(stored_hash, password):
            return jsonify({"error": "Invalid email or password"}), 401

        session["user_id"] = str(users[0]["id"])
        session["email"] = users[0]["email"]

        return jsonify({"message": "Login successful", "redirect_url": url_for('dashboard')}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Renders the dashboard if the user is logged in."""
    if "user_id" not in session:
        return redirect(url_for('signin'))  # Redirect if not logged in
    return render_template('dashboard/dashboard.html')


# ✅ Serves the homepage page
@app.route('/homepage', methods=['GET'])
def homepage():
    return render_template('dashboard/homepage.html')


# ✅ Serves the settings page
@app.route('/settings', methods=['GET'])
def settings():
    return render_template('dashboard/settings.html')


# ✅ Serves the profile page
@app.route('/profile', methods=['GET'])
def profile():
    return render_template('dashboard/profile.html')


# ✅ Serves the tasks page
@app.route('/tasks', methods=['GET'])
def tasks():
    return render_template('dashboard/tasks.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
