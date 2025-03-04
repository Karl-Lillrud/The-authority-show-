from pymongo import MongoClient
import os
from dotenv import load_dotenv
 
# Load environment variables
load_dotenv()
 
# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"
 
# Initialize MongoDB Client
client = MongoClient(MONGODB_URI)
database = client[DATABASE_NAME]
 
# Define collection names
collections = [
    "Teams",
    "Subscriptions",
    "Podtasks",
    "Podcasts",
    "Guests",
    "Episodes",
    "Credits",
    "Accounts",
    "UsersToTeams",
    "Edits",
    "Users"
]
 
# Create collections if they do not exist
for collection_name in collections:
    if collection_name not in database.list_collection_names():
        database.create_collection(collection_name)
 
print("Collections created successfully.")
 