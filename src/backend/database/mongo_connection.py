from pymongo import MongoClient
from flask import Blueprint
import os
from dotenv import load_dotenv
import logging
from gridfs import GridFS

mongo_bp = Blueprint("mongo_bp", __name__)

# Load environment variables
load_dotenv()


# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"
COLLECTION_NAME = "Users"

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
    fs = GridFS(database)  # Initialize GridFS
    logger.info("MongoDB connection and GridFS initialized successfully.")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB or initialize GridFS: {e}")
    raise

# Functions to access MongoDB and GridFS
def get_db():
    return database

def get_fs():
    return fs