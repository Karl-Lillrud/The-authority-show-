from flask import Flask, render_template, request, jsonify, url_for, session
from azure.cosmos import CosmosClient
from register import register_bp  # ✅ Import register blueprint
from dotenv import load_dotenv
import os
import traceback  # Add this for error logging

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
    """Handles sign-in and renders the sign-in page."""
    if request.method == 'GET':
        return render_template('signin.html')

    try:
        if not request.is_json:
            return jsonify({"error": "Invalid request format. Expected JSON."}), 400

        data = request.get_json()
        required_fields = {"email", "password"}
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields: email, password"}), 400

        email = data["email"].lower().strip()
        password = data["password"]

        # Query Cosmos DB for the user
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters = [{"name": "@email", "value": email}]
        users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        from werkzeug.security import check_password_hash
        if not users or not check_password_hash(users[0]["passwordHash"], password):
            return jsonify({"error": "Invalid email or password"}), 401

        # Set session
        session["user_id"] = users[0]["id"]
        session["email"] = users[0]["email"]

        return jsonify({"message": "Login successful", "redirect_url": url_for('dashboard')}), 200

    except Exception as e:
        print("Error during login:", str(e))
        print(traceback.format_exc())  # Print full error traceback
        return jsonify({"error": "Internal Server Error"}), 500  # Return JSON instead of HTML


@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgot_password():
    return render_template('forgotpassword/forgot-password.html')  # Remove extra subfolder

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
