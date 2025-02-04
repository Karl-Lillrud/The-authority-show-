from flask import Flask, render_template, request, jsonify, redirect, url_for 
from azure.cosmos import CosmosClient
from cosmos_routes import (
    cosmos_bp,  # Import the blueprint for routing the DB methods
    create_item,
    get_items
)
from dotenv import load_dotenv
import os
import uuid
import hashlib

load_dotenv()

app = Flask(__name__, template_folder='templates')
app.register_blueprint(cosmos_bp, url_prefix='/api')

@app.route('/test-db', methods=['GET'])
def test_db_connection():
    try:
        # ✅ Attempt to fetch an item from the database
        test_data, status = get_items()

        if status != 200:
            return jsonify({"error": "Failed to fetch data from database"}), 500

        return jsonify({"message": "Database connection successful", "sample_data": test_data}), 200

    except Exception as e:
        return jsonify({"error": f"Database connection failed: {str(e)}"}), 500

COSMOSDB_URI = os.getenv("COSMOS_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOS_KEY")
DATABASE_ID = "podmanagedb"
CONTAINER_ID = "users"

# Initialize Cosmos client
client = CosmosClient(COSMOSDB_URI, credential=COSMOSDB_KEY)
database = client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)

from flask import Flask, render_template, request, jsonify, url_for

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from azure.cosmos import CosmosClient
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")  # Required for session storage

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

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from azure.cosmos import CosmosClient
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")  # Required for session storage

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

@app.route('/', methods=['GET', 'POST'])
def signin():
    """Handles sign-in and renders the sign-in page."""
    if request.method == 'GET':
        return render_template('signin.html')

    if not request.is_json:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400

    data = request.get_json()

    required_fields = {"email", "password"}
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields: email, password"}), 400

    email = data["email"].lower().strip()
    password = data["password"]

    # ✅ Query Cosmos DB for the user directly using email
    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": email}]
    users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

    if not users:
        return jsonify({"error": "Invalid email or password"}), 401

    user = users[0]

    # ✅ Fix password verification (use `check_password_hash`)
    if not check_password_hash(user["passwordHash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    # ✅ Store user session
    session["user_id"] = user["id"]
    session["email"] = user["email"]

    return jsonify({"message": "Login successful", "redirect_url": url_for('dashboard')}), 200

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Renders the dashboard if the user is logged in."""
    if "user_id" not in session:
        return redirect(url_for('signin'))  # Redirect if not logged in
    return render_template('dashboard.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register/register.html')  # ✅ Shows registration form when accessed via GET

    # ✅ Handle registration only when method is POST
    if request.method == 'POST':
        if not request.is_json:
            return jsonify({"error": "Invalid request format. Expected JSON."}), 400

        data = request.get_json()

        # Ensure required fields exist
        required_fields = {"email", "password"}
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields: email, password"}), 400

        # Validate data types
        if not isinstance(data["email"], str) or not isinstance(data["password"], str):
            return jsonify({"error": "Invalid Entry. 'email' and 'password' must be strings."}), 400

        # Hash the password before storing it
        hashed_password = hashlib.sha256(data["password"].encode()).hexdigest()

        # Generate a unique user ID
        user_id = str(uuid.uuid4())

        # Prepare user data for storage
        user_data = {
            "id": user_id,
            "email": data["email"],
            "password": hashed_password,  # Storing hashed password securely
        }

        # Store in Cosmos DB
        response, status = create_item(user_data)

        return jsonify(response), status
    
    return render_template('signin.html')

@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgotpassword/forgot-password.html')  # ✅ Renders form for password reset

    return jsonify({"message": "Password reset feature coming soon"}), 200  # ✅ Added a response for POST requests


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
