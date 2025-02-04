import logging
import os
from flask import Blueprint, request, jsonify
from azure.cosmos import CosmosClient, PartitionKey
from datetime import datetime, timezone

# Define the blueprint
cosmos_bp = Blueprint('cosmos_bp', __name__)

# Retrieve Cosmos DB credentials from environment variables (set as GitHub secrets)
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
COSMOS_KEY = os.environ.get("COSMOS_KEY")

if not COSMOS_ENDPOINT or not COSMOS_KEY:
    raise ValueError("Cosmos DB credentials are missing. Ensure COSMOS_ENDPOINT and COSMOS_KEY are set as environment variables.")

DATABASE_NAME = "podmanagedb"
CONTAINER_NAME = "users"

# Initialize Cosmos client securely
def init_cosmos_db():
    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.create_database_if_not_exists(id=DATABASE_NAME)
        container = database.create_container_if_not_exists(
            id=CONTAINER_NAME,
            partition_key=PartitionKey(path="/email"),
            offer_throughput=400
        )
        logging.info("✅ Cosmos DB connection initialized successfully.")
    except Exception as e:
        logging.error(f"❌ Error initializing Cosmos DB: {e}")
        raise e

# Initialize the database on startup
init_cosmos_db()

# Logging setup
logging.basicConfig(level=logging.DEBUG)

def current_timestamp():
    return datetime.now(timezone.utc).isoformat()

def create_item(data):
    try:
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
        query = "SELECT * FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        return jsonify(items), 200
    except Exception as e:
        logging.error(f"Error retrieving items: {e}")
        return {"error": str(e)}, 500

@cosmos_bp.route('/items', methods=['GET'])
def handle_get_items():
    return get_items()

@cosmos_bp.route('/items', methods=['POST'])
def handle_create_item():
    data = request.get_json()
    if not data:
        return {"error": "Invalid or missing JSON data."}, 400
    return create_item(data)
