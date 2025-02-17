from pymongo import MongoClient
from flask import Blueprint
import os
from dotenv import load_dotenv

mongo_bp = Blueprint("mongo_bp", __name__)

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "podmanagedb"
COLLECTION_NAME = "users"

if not MONGO_URI:
    raise ValueError("MongoDB URI is missing.")

# Initialize MongoDB Client
client = MongoClient(MONGO_URI)
database = client[DATABASE_NAME]
collection = database[COLLECTION_NAME]
