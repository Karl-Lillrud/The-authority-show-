from pymongo import MongoClient
from flask import Blueprint
import os
from dotenv import load_dotenv
import logging

"""
MongoDB Connection Module

This module handles the connection to MongoDB using environment variables.
It initializes the connection and logs any issues that may arise.

Features:
- Loads MongoDB URI from environment variables.
- Establishes a connection with the MongoDB database.
- Provides a collection reference for further operations.
"""

# Define Flask Blueprint for MongoDB operations
mongo_bp = Blueprint("mongo_bp", __name__)

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"
COLLECTION_NAME = "User"

# Ensure the MongoDB URI is provided
if not MONGODB_URI:

    raise ValueError("MongoDB URI is missing. Please set MONGODB_URI in your environment variables.")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB Client and Collection
try:

    logger.info("Connecting to MongoDB...")
    client = MongoClient(MONGODB_URI)
    database = client[DATABASE_NAME]
    collection = database[COLLECTION_NAME]
    logger.info("MongoDB connection established successfully.")

except Exception as e:

    logger.error(f"Failed to connect to MongoDB: {e}")
    raise
