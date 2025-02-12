# register.py
from flask import Blueprint, request, jsonify, url_for, render_template
from azure.cosmos import CosmosClient, PartitionKey, exceptions
import os
import uuid
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from datetime import datetime

register_bp = Blueprint('register_bp', __name__)
load_dotenv()

COSMOSDB_URI = os.getenv("COSMOS_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOS_KEY")
DATABASE_ID = "podmanagedb"

if not COSMOSDB_URI or not COSMOSDB_KEY:
    raise ValueError("Cosmos DB credentials are missing.")

client = CosmosClient(COSMOSDB_URI, COSMOSDB_KEY)
database = client.get_database_client(DATABASE_ID)

# Create the "users" container if it doesn't exist
users_container = database.create_container_if_not_exists(
    id="users",
    partition_key=PartitionKey(path="/email"),
    offer_throughput=400
)

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register/register.html')
    if request.content_type == "application/json":
        data = request.get_json()
    else:
        data = request.form  
    if "email" not in data or "password" not in data:
        return jsonify({"error": "Missing email or password"}), 400
    email = data["email"].lower().strip()
    password = data["password"]
    hashed_password = generate_password_hash(password)
    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": email}]
    existing_users = list(users_container.query_items(
        query=query, parameters=parameters, enable_cross_partition_query=True
    ))
    if existing_users:
        return jsonify({"error": "Email already registered."}), 409
    user_document = {
        "id": str(uuid.uuid4()),
        "email": email,
        "passwordHash": hashed_password,
        "createdAt": datetime.utcnow().isoformat(),
        "partitionKey": email
    }
    try:
        users_container.create_item(body=user_document)
        return jsonify({"message": "Registration successful!", "redirect_url": url_for('signin', _external=True)}), 201
    except exceptions.CosmosHttpResponseError as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
