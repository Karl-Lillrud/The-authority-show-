from azure.cosmos import CosmosClient
from flask import Blueprint
import os
from dotenv import load_dotenv

cosmos_bp = Blueprint('cosmos_bp', __name__)

# Load environment variables
load_dotenv()

# CosmosDB Configuration
COSMOSDB_URI = os.getenv("COSMOS_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOS_KEY")
DATABASE_ID = "podmanagedb"
CONTAINER_ID = "users"

if not COSMOSDB_URI or not COSMOSDB_KEY:
    raise ValueError("Cosmos DB credentials are missing.")

# Initialize CosmosDB Client
client = CosmosClient(COSMOSDB_URI, COSMOSDB_KEY)
database = client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)
