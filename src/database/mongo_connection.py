from pymongo import MongoClient
from flask import Blueprint
import os
from dotenv import load_dotenv

mongo_bp = Blueprint("mongo_bp", __name__)

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "podmanagedb"
COLLECTION_NAME = "users"

if not MONGODB_URI:
    raise ValueError("MongoDB URI is missing.")

# Initialize MongoDB Client
client = MongoClient(MONGODB_URI)
database = client[DATABASE_NAME]
collection = database[COLLECTION_NAME]
