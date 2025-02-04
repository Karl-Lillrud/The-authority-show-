from flask import Flask, render_template, request, jsonify, redirect, url_for 
from azure.cosmos import CosmosClient
from cosmos_routes import (
    cosmos_bp,  # Import the blueprint for routing the DB methods
    create_item,
    get_items
)
import os
import uuid
import hashlib

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

COSMOSDB_URI = os.getenv("COSMOSDB_URI")
COSMOSDB_KEY = os.getenv("COSMOSDB_KEY")
DATABASE_ID = "podmanagedb"
CONTAINER_ID = "Users"

# Initialize Cosmos client
client = CosmosClient(COSMOSDB_URI, credential=COSMOSDB_KEY)
database = client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)

@app.route('/', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return render_template('signin.html')  # ✅ Loads signin.html when visiting root

    # ✅ Handle login only when method is POST
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
            return jsonify({"error": "Invalid data types. 'email' and 'password' must be strings."}), 400

        # Hash the input password to compare with the stored hashed password
        hashed_password = hashlib.sha256(data["password"].encode()).hexdigest()

        # Query the database for the user
        users, status = get_items()

        if status != 200:
            return jsonify({"error": "Database query failed"}), 500

        user = next((u for u in users if u["email"] == data["email"]), None)

        if not user or user["password"] != hashed_password:
            return jsonify({"error": "Invalid email or password"}), 401

        # ✅ Redirect the user to the dashboard upon successful login
        return redirect(url_for('dashboard'))
    
    return render_template('signin.html')


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

@app.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('dashboard/dashboard.html')  # ✅ Renders dashboard when accessed via GET

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
