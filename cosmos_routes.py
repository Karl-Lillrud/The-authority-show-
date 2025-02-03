import logging
from flask import Blueprint, request, jsonify
from azure.cosmos import CosmosClient, PartitionKey
from datetime import datetime, timezone
import os

# Define the blueprint
cosmos_bp = Blueprint('cosmos_bp', __name__)

# Cosmos DB configuration
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "https://podmanagedb.documents.azure.com:443/")
COSMOS_KEY = os.environ.get("COSMOS_KEY", "MiLps5254nsIyfOquJ0NTPrGiPoVDbzMO8cFzUoc8EWimIbMVgjlOxl2rXFk4wjb8Xe6jzgt0tqWACDbUnMLqw==")
DATABASE_NAME = "podmanager"
CONTAINER_NAME = "users"

# Initialize Cosmos client and ensure DB and Container exist
def init_cosmos_db():
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    try:
        database = client.create_database_if_not_exists(id=DATABASE_NAME)
        container = database.create_container_if_not_exists(
            id=CONTAINER_NAME,
            partition_key=PartitionKey(path="/id"),
            offer_throughput=400
        )
        logging.info("Database and container initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing Cosmos DB: {e}")
        raise e

# Initialize DB and Container
init_cosmos_db()

# Logging setup
logging.basicConfig(level=logging.DEBUG)

def current_timestamp():
    return datetime.now(timezone.utc).isoformat()

def validate_json(data):
    required_fields = {"id", "email", "password"}
    if not all(field in data for field in required_fields):
        return False, "Missing required fields: " + ", ".join(required_fields - data.keys())
    if not isinstance(data["id"], str) or not isinstance(data["email"], str) or not isinstance(data["password"], str):
        return False, "Invalid data types. 'id', 'email', and 'password' must be strings."
    return True, None

def create_item(data):
    try:
        is_valid, error_message = validate_json(data)
        if not is_valid:
            return {"error": error_message}, 400
        data['created_at'] = current_timestamp()
        logging.debug(f"Creating item: {data}")
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        container.create_item(body=data)
        return data, 201
    except Exception as e:
        logging.error(f"Error creating item: {e}")
        return {"error": str(e)}, 500

def get_items():
    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        items = list(container.read_all_items())
        return items, 200
    except Exception as e:
        logging.error(f"Error fetching items: {e}")
        return {"error": str(e)}, 500

@cosmos_bp.route('/items', methods=['POST'])
def create_item_route():
    if not request.is_json:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400
    data = request.get_json()
    response, status = create_item(data)
    return jsonify(response), status

@cosmos_bp.route('/items', methods=['GET'])
def get_items_route():
    response, status = get_items()
    return jsonify(response), status
