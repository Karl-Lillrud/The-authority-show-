from pymongo import MongoClient
from flask import Blueprint
import os
from dotenv import load_dotenv
import logging

mongo_bp = Blueprint("mongo_bp", __name__)

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"
USERS_COLLECTION_NAME = "Users"
MAILING_LIST_COLLECTION_NAME = "MailingList"  # Add MailingList collection
SUBSCRIPTIONS_LIST_COLLECTION = "subscriptions_collection"

if not MONGODB_URI:
    raise ValueError("MongoDB URI is missing.")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB Client
try:
    client = MongoClient(MONGODB_URI)
    database = client[DATABASE_NAME]
    
    # Initialize the collections (same name 'collection' for both)
    collection = database[USERS_COLLECTION_NAME]  # Users collection
    mailing_list_collection = database[MAILING_LIST_COLLECTION_NAME]  # MailingList collection
    subscriptions_collection = database[SUBSCRIPTIONS_LIST_COLLECTION]
    
    logger.info("MongoDB connection established successfully.")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise
