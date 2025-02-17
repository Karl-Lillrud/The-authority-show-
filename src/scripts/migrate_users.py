from azure.cosmos import CosmosClient
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# CosmosDB Configuration
COSMOSDB_URI = os.getenv("COSMOS_ENDPOINT")
COSMOSDB_KEY = os.getenv("COSMOS_KEY")
DATABASE_ID = "podmanagedb"
CONTAINER_ID = "users"

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGO_DATABASE_NAME = "podmanagedb"
MONGO_COLLECTION_NAME = "users"

# Initialize CosmosDB Client
if COSMOSDB_URI is None or COSMOSDB_KEY is None:
    raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY environment variables must be set")

cosmos_client = CosmosClient(COSMOSDB_URI, COSMOSDB_KEY)
cosmos_database = cosmos_client.get_database_client(DATABASE_ID)
cosmos_container = cosmos_database.get_container_client(CONTAINER_ID)

# Initialize MongoDB Client
mongo_client = MongoClient(MONGODB_URI)
mongo_database = mongo_client[MONGO_DATABASE_NAME]
mongo_collection = mongo_database[MONGO_COLLECTION_NAME]

# Fetch all users from CosmosDB
cosmos_users = list(cosmos_container.read_all_items())

# Transform and insert users into MongoDB
for user in cosmos_users:
    mongo_user = {
        "_id": user["id"],
        "email": user["email"],
        "passwordHash": user["passwordHash"],
        "createdAt": user["createdAt"],
    }
    mongo_collection.insert_one(mongo_user)

print("Migration completed successfully.")
