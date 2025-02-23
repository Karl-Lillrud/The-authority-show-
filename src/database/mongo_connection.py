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
COLLECTION_NAME = "Podmanager"

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
    logger.info("MongoDB connection established successfully.")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise
