from pymongo import MongoClient
from flask import Blueprint
import os
from dotenv import load_dotenv
import logging
from gridfs import GridFS

# Create a blueprint for MongoDB (this can be used for modular Flask apps)
mongo_bp = Blueprint("mongo_bp", __name__)

# Load environment variables from .env
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"  # Database name
COLLECTION_NAME = "Users"  # Collection for users
PODCAST_NAME = "Podcasts"  # Collection for podcasts
EPISODE_NAME = "Episodes"  # Collection for episodes
MAILING_LIST_COLLECTION_NAME = "MailingList"  # Mailing List collection
SUBSCRIPTIONS_LIST_COLLECTION = "subscriptions_collection"  # Subscriptions collection

# Raise an error if MONGODB_URI is missing
if not MONGODB_URI:
    raise ValueError("MongoDB URI is missing.")

# Initialize logging for MongoDB connection
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB Client and GridFS
try:
    # Create a MongoDB client instance using the URI
    client = MongoClient(MONGODB_URI)
    
    # Select the database using DATABASE_NAME
    database = client[DATABASE_NAME]
    
    # Access individual collections
    collection = database[COLLECTION_NAME]  # Users collection
    podcasts = database[PODCAST_NAME]  # Podcasts collection
    episodes = database[EPISODE_NAME]  # Episodes collection
    mailing_list_collection = database[MAILING_LIST_COLLECTION_NAME]  # Mailing List collection
    subscriptions_collection = database[SUBSCRIPTIONS_LIST_COLLECTION]  # Subscriptions collection
    
    # Initialize GridFS for file storage
    fs = GridFS(database)
    
    logger.info("MongoDB connection and GridFS initialized successfully.")
except Exception as e:
    # Log error if connection fails
    logger.error(f"Failed to connect to MongoDB or initialize GridFS: {e}")
    raise

# Functions to access MongoDB and GridFS

def get_db():
    """Returns the database connection object"""
    return database

def get_fs():
    """Returns the GridFS connection object"""
    return fs

def get_collection(collection_name):
    """Helper function to get a collection by its name"""
    return database[collection_name]

def get_podcasts_collection():
    """Returns the Podcasts collection"""
    return podcasts

def get_episodes_collection():
    """Returns the Episodes collection"""
    return episodes

def get_users_collection():
    """Returns the Users collection"""
    return collection
