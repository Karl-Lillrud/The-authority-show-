from flask import Flask, render_template, request, redirect, jsonify, url_for, session
from azure.cosmos import CosmosClient
from register import register_bp  # ✅ Import register blueprint
from dotenv import load_dotenv
import os
import traceback  # Add this for error logging

app = Flask(__name__)

@app.before_request
def force_https():
    """Redirect all HTTP requests to HTTPS"""
    if request.url.startswith("http://"):
        secure_url = request.url.replace("http://", "https://")
        return redirect(secure_url, code=301)

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY")  # Use an env variable or a fallback key
app.config["SESSION_TYPE"] = "filesystem"  # Store session data
app.config["SESSION_PERMANENT"] = False

app.register_blueprint(register_bp)

# Azure Cosmos DB Configuration
COSMOSDB_URI = os.getenv("COSMOS_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOS_KEY")
DATABASE_ID = "podmanagedb"
CONTAINER_ID = "users"

if not COSMOSDB_URI or not COSMOSDB_KEY:
    raise ValueError("Cosmos DB credentials are missing.")

# Initialize Cosmos client
client = CosmosClient(COSMOSDB_URI, COSMOSDB_KEY)
database = client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)

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
@app.route('/accountsettings', methods=['GET'])
def accountsettings():
    return render_template('dashboard/accountsettings.html')

# ✅ Serves the profile page
@app.route('/podcastmanagement', methods=['GET'])
def podcastmanagement():
    return render_template('dashboard/podcastmanagement.html')

# ✅ Serves the tasks page
@app.route('/taskmanagement', methods=['GET'])
def taskmanagement():
    return render_template('dashboard/taskmanagement.html')



@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgot_password():
    return render_template('forgotpassword/forgot-password.html')  # Remove extra subfolder

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
