from flask import Flask, render_template, request, jsonify, url_for, session, redirect
from azure.cosmos import CosmosClient
from register import register_bp
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
import smtplib
from email.mime.text import MIMEText

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY")
app.config['PREFERRED URL SCHEME'] = 'https'
app.register_blueprint(register_bp)

APP_ENV = os.getenv("APP_ENV", "production")  # Default to production

# CosmosDB Configuration
COSMOSDB_URI = os.getenv("COSMOS_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOS_KEY")
DATABASE_ID = "podmanagedb"
CONTAINER_ID = "users"

if not COSMOSDB_URI or not COSMOSDB_KEY:
    raise ValueError("Cosmos DB credentials are missing.")

# Initialize CosmosDB Client
client = CosmosClient(COSMOSDB_URI, COSMOSDB_KEY)
database = client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)

PI_BASE_URL = "http://127.0.0.1:8000" if APP_ENV == "local" else "https://app.podmanager.ai"

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# 📌 Step 1: Forgot Password
@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        # Render the forgot password page if accessed via GET
        return render_template('forgotpassword/forgot-password.html')

    # Ensure proper content type
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415  

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    email = data.get("email", "").strip().lower()

    print(f"🔍 Checking for email: {email}")  # Debugging log

    query = "SELECT * FROM c WHERE LOWER(c.email) = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

    if not users:
        return jsonify({"error": "No account found with that email"}), 404

    reset_code = str(random.randint(100000, 999999))

    user = users[0]
    user["reset_code"] = reset_code
    container.upsert_item(user)

    try:
        send_reset_email(email, reset_code)
        return jsonify({"message": "Reset code sent successfully.", "redirect_url": url_for('enter_code')}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500


# 📌 Step 2: Enter Reset Code
@app.route('/enter-code', methods=['GET', 'POST'])
def enter_code():
    print(f"🔍 Request Headers: {request.headers}")  # ✅ Debugging
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

    print(f"🔍 Checking Email: {email}, Code: {entered_code}")  # ✅ Debugging

    query = "SELECT * FROM c WHERE LOWER(c.email) = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

    if not users or users[0].get("reset_code") != entered_code:
        return jsonify({"error": "Invalid or expired reset code."}), 400

    print("✅ Code Verified, Redirecting to Reset Password")

    return jsonify({"message": "Code is Valid.", "redirect_url": url_for('reset_password')}), 200


# 📌 Step 3: Reset Password
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        return render_template('forgotpassword/reset-password.html')  # ✅ Allow GET request

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
    user.pop("reset_code", None)
    container.upsert_item(user)

    return jsonify({"message": "Password updated successfully.", "redirect_url": url_for('signin')}), 200


# 📌 Send Reset Email
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
    try:
        if request.content_type != "application/json":
            return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415  

        data = request.get_json()
        email = data.get("email", "").strip().lower()

        print(f"🔍 Resending code for email: {email}")

        query = "SELECT * FROM c WHERE LOWER(c.email) = @email"
        parameters = [{"name": "@email", "value": email}]
        users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if not users:
            return jsonify({"error": "No account found with that email"}), 404

        # Generate a new reset code
        reset_code = str(random.randint(100000, 999999))
        user = users[0]
        user["reset_code"] = reset_code
        container.upsert_item(user)

        send_reset_email(email, reset_code)  # ✅ Send email

        return jsonify({"message": "New reset code sent successfully."}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to resend code: {str(e)}"}), 500

# 📌 Sign-in Route
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
    users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

    if not users or not check_password_hash(users[0]["passwordHash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = str(users[0]["id"])
    session["email"] = users[0]["email"]
    session.permanent = True

    return jsonify({"message": "Login successful", "redirect_url": "/dashboard"}), 200

# 📌 Dashboard
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for('signin'))
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