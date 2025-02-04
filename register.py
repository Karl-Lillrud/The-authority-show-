from flask import Flask, request, jsonify, url_for
from azure.cosmos import CosmosClient, exceptions
import os
import uuid
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Azure Cosmos DB Configuration
COSMOSDB_URI = os.getenv("COSMOS_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOS_KEY")
DATABASE_ID = "podmanagedb"
CONTAINER_ID = "users"

if not COSMOSDB_URI or not COSMOSDB_KEY:
    raise ValueError("Cosmos DB credentials are missing.")

# Initialize Cosmos DB client
client = CosmosClient(COSMOSDB_URI, COSMOSDB_KEY)
database = client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)

@app.route('/register', methods=['POST'])
def register():
    """Handles user registration."""
    if request.is_json:
        data = request.get_json()
    else:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400

    if "email" not in data or "password" not in data:
        return jsonify({"error": "Missing email or password"}), 400

    email = data["email"].lower().strip()
    password = data["password"]
    hashed_password = generate_password_hash(password)  # ✅ Use proper password hashing

    # Check if user already exists
    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": email}]
    existing_users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

    if existing_users:
        return jsonify({"error": "Email already registered."}), 409

    # Create user document
    user_document = {
        "id": str(uuid.uuid4()),
        "email": email,
        "passwordHash": hashed_password,  # ✅ Correct hashing method
        "createdAt": datetime.utcnow().isoformat(),
        "partitionKey": email
    }

    try:
        container.create_item(body=user_document)
        return jsonify({"message": "Registration successful!"}), 201  # ✅ Show success message
    except exceptions.CosmosHttpResponseError as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
