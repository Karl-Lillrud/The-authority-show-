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
COLLECTION_NAME = "Users"
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
    collection = database[COLLECTION_NAME]
    mailing_list_collection = database[MAILING_LIST_COLLECTION_NAME]  # MailingList collection
    subscriptions_collection = database[SUBSCRIPTIONS_LIST_COLLECTION]
    logger.info("MongoDB connection initialized successfully.")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Functions to access MongoDB
def get_db():
    return database

# Function to get the upload folder path
def get_upload_folder():
    return os.getenv("UPLOAD_FOLDER", r"C:\Users\sarwe\Deskto")