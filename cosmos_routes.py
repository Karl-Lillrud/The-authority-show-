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
DATABASE_NAME = os.environ.get("COSMOS_DATABASE", "podmanagedb")
CONTAINER_NAME = os.environ.get("COSMOS_CONTAINER", "users")

# Initialize Cosmos client
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.create_database_if_not_exists(id=DATABASE_NAME)
container = database.create_container_if_not_exists(
id=CONTAINER_NAME,
partition_key=PartitionKey(path="/id"),
offer_throughput=400
)

# Logging setup
logging.basicConfig(level=logging.DEBUG)

def current_timestamp():
    return datetime.now(timezone.utc).isoformat()

def validate_json(data):
    """ Ensure that the incoming JSON contains the required fields. """
    required_fields = {"id", "email", "password"}
    
    # Check if all required fields are present
    if not all(field in data for field in required_fields):
        return False, "Missing required fields: " + ", ".join(required_fields - data.keys())
    
    # Validate data types
    if not isinstance(data["id"], int) or not isinstance(data["email"], str) or not isinstance(data["password"], str):
        return False, "Invalid data types. 'id' must be an integer, 'email' and 'password' must be strings."

    return True, None

# Function to create an item
def create_item(data):
    try:
        # Validate JSON structure
        is_valid, error_message = validate_json(data)
        if not is_valid:
            return {"error": error_message}, 400
        
        # Add timestamp
        data['created_at'] = current_timestamp()

        # Log request
        logging.debug(f"Creating item: {data}")

        # Insert into CosmosDB
        container.create_item(body=data)
        
        return data, 201

    except Exception as e:
        logging.error(f"Error creating item: {e}")
        return {"error": str(e)}, 500

# Function to get all items
def get_items():
    try:
        query = "SELECT * FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        return items, 200
    except Exception as e:
        logging.error(f"Error fetching items: {e}")
        return {"error": str(e)}, 500

# Function to get a single item by ID
def get_item_by_id(item_id):
    try:
        item = container.read_item(item=item_id, partition_key=item_id)
        return item, 200
    except Exception as e:
        logging.error(f"Error fetching item {item_id}: {e}")
        return {"error": str(e)}, 500

# Function to update an item
def update_item(item_id, updated_data):
    try:
        existing_item = container.read_item(item=item_id, partition_key=item_id)

        for key, value in updated_data.items():
            existing_item[key] = value
        
        existing_item['updated_at'] = current_timestamp()
        container.replace_item(item=existing_item, body=existing_item)

        return existing_item, 200

    except Exception as e:
        logging.error(f"Error updating item {item_id}: {e}")
        return {"error": str(e)}, 500

# Function to delete an item
def delete_item(item_id):
    try:
        container.delete_item(item=item_id, partition_key=item_id)
        deletion_time = current_timestamp()
        return {"message": f"Item {item_id} deleted", "deleted_at": deletion_time}, 200
    except Exception as e:
        logging.error(f"Error deleting item {item_id}: {e}")
        return {"error": str(e)}, 500

# Flask routes using the functions
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

@cosmos_bp.route('/items/<item_id>', methods=['GET'])
def get_item_route(item_id):
    response, status = get_item_by_id(item_id)
    return jsonify(response), status

@cosmos_bp.route('/items/<item_id>', methods=['PUT'])
def update_item_route(item_id):
    if not request.is_json:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400
    updated_data = request.get_json()
    response, status = update_item(item_id, updated_data)
    return jsonify(response), status

@cosmos_bp.route('/items/<item_id>', methods=['DELETE'])
def delete_item_route(item_id):
    response, status = delete_item(item_id)
    return jsonify(response), status
