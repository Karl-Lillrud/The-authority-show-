import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, redirect, url_for, render_template
from azure.cosmos import CosmosClient, exceptions
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Blueprint
register_bp = Blueprint('register_bp', __name__)

# Azure Cosmos DB configuration
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
COSMOS_KEY = os.environ.get("COSMOS_KEY")
DATABASE_NAME = "podmanagedb"
CONTAINER_NAME = "users"

if not COSMOS_ENDPOINT or not COSMOS_KEY:
    raise ValueError("Cosmos DB credentials are missing. Ensure COSMOS_ENDPOINT and COSMOS_KEY are set.")

# Initialize Cosmos DB client (used in app.py)
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

@register_bp.route('/register', methods=['POST'])
def register():
    if not request.is_json:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400
    
    data = request.get_json()

    # Validate input
    if not data or 'name' not in data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Missing required fields: name, email, password."}), 400
    
    name = data['name']
    email = data['email']
    password = data['password']

    # Hash the password
    password_hash = generate_password_hash(password)

    # Check if the user already exists
    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": email}]
    existing_users = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

    if existing_users:
        return jsonify({"error": "Email already registered."}), 409

    # Create user document
    user_document = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "passwordHash": password_hash,
        "createdAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    try:
        container.create_item(body=user_document)
        return jsonify({"message": "User registered successfully."}), 201
    except exceptions.CosmosHttpResponseError as e:
        return jsonify({"error": str(e)}), 500