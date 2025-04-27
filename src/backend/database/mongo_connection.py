from pymongo import MongoClient
from flask import Blueprint
import os
from dotenv import load_dotenv
import logging
from gridfs import GridFS
# from colorama import Fore, Style, init  # Import colorama for styled logs

mongo_bp = Blueprint("mongo_bp", __name__)

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"
COLLECTION_NAME = "Users"
PODCAST_NAME = "Podcasts"
EPISODE_NAME = "Episodes"
CREDITS = "Credits"
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
    podcasts = database[PODCAST_NAME]
    episodes = database[EPISODE_NAME]
    credits = database[CREDITS]
    mailing_list_collection = database[MAILING_LIST_COLLECTION_NAME]
    subscriptions_collection = database[SUBSCRIPTIONS_LIST_COLLECTION]
    fs = GridFS(database)  # Initialize GridFS
    logger.info("MongoDB connected successfully!")
except Exception as ez:
    logger.error("Failed to connect to MongoDB or initialize GridFS: {e}")
    raise


#Functions to access MongoDB and GridFS
def get_db():
    return database


def get_fs():
    return fs
