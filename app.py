from flask import Flask, render_template, request, jsonify, url_for, session
from azure.cosmos import CosmosClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from register import register_bp
import os
import random
import smtplib
from email.mime.text import MIMEText

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY")

app.register_blueprint(register_bp)

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


# 📌 Step 1: User Requests Password Reset
@app.route('/forgotpassword', methods=['GET','POST'])
def forgot_password():
    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415  # 415 = Unsupported Media Type

    data = request.get_json()
    email = data.get("email", "").strip().lower()

    # Check if the user exists
    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

    if not users:
        return jsonify({"error": "No account found with that email"}), 404

    reset_code = str(random.randint(100000, 999999))

    # Store reset code in the database
    user = users[0]
    user["reset_code"] = reset_code
    container.upsert_item(user)

    # Send reset code via email
    try:
        send_reset_email(email, reset_code)
        return jsonify({
            "message": "Reset code sent successfully.",
            "redirect_url": url_for('enter_code')
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 📌 Step 2: User Enters Reset Code
@app.route('/enter-code', methods=['POST'])
def enter_code():
    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    email = data.get("email", "").strip().lower()
    entered_code = data.get("code", "").strip()

    # Retrieve user from the database
    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

    if not users or users[0].get("reset_code") != entered_code:
        return jsonify({"error": "Invalid or expired reset code."}), 400

    return jsonify({
        "message": "Code verified. You can now reset your password.",
        "redirect_url": url_for('reset_password')
    }), 200



# 📌 Step 3: User Resets Password
@app.route('/reset-password', methods=['POST'])
def reset_password():
    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    email = data.get("email", "").strip().lower()
    new_password = data.get("password", "")

    # Retrieve user from the database
    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

    if not users:
        return jsonify({"error": "User not found."}), 404

    user = users[0]
    user["passwordHash"] = generate_password_hash(new_password)
    user.pop("reset_code", None)  # Remove reset code after use
    container.upsert_item(user)

    return jsonify({
        "message": "Password updated successfully.",
        "redirect_url": url_for('signin')
    }), 200

# 📌 Function to Send Email
def send_reset_email(email, reset_code):
    try:
        msg = MIMEText(f"Your password reset code is: {reset_code}\nUse this code to reset your password.")
        msg["Subject"] = "Password Reset Request"
        msg["From"] = EMAIL_USER
        msg["To"] = email

        print(f"📧 Attempting to send reset email to {email} via {SMTP_SERVER}:{SMTP_PORT}")

        # Connect to SMTP Server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.set_debuglevel(1)  # Enable debugging output for SMTP connection
            server.starttls()  # Secure the connection
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, email, msg.as_string())

        print("✅ Reset email sent successfully!")

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication Error: {e}")
    except smtplib.SMTPConnectError as e:
        print(f"❌ SMTP Connection Error: {e}")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
    except Exception as e:
        print(f"❌ General Email Sending Error: {e}")


app.config['PREFERRED URL SCHEME'] = 'https'
    
@app.route('/', methods=['GET'])
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    try:
        if request.method == 'GET':
            return render_template('signin.html')

        data = request.get_json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        print(f"Login attempt: {email}")

        # Query CosmosDB
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters = [{"name": "@email", "value": email}]
        users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        print(f"Users found: {users}")

        if not users:
            print("❌ User not found.")
            return jsonify({"error": "Invalid email or password"}), 401

        from werkzeug.security import check_password_hash

        # **Debug password comparison**
        stored_hash = users[0].get("passwordHash", "")
        print(f"Stored Hash: {stored_hash}")
        print(f"Entered Password: {password}")

        if not check_password_hash(stored_hash, password):
            print("❌ Password mismatch.")
            return jsonify({"error": "Invalid email or password"}), 401

        print(f"✅ User {email} logged in successfully.")

        session["user_id"] = str(users[0]["id"])
        session["email"] = users[0]["email"]

        return jsonify({"message": "Login successful", "redirect_url": url_for('dashboard')}), 200

    except Exception as e:
        print("Error during login:", str(e))
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

