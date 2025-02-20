from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"

if not MONGODB_URI:

    raise ValueError("MongoDB URI is missing.")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB Client
try:

    client = MongoClient(MONGODB_URI)
    database = client[DATABASE_NAME]
    logger.info("MongoDB connection established successfully.")

except Exception as e:

    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Define collections and their schema
collections = {

    "Credit": {
        "ID": str,
        "credits": int,
        "unclaimed_credits": int,
        "referral_bonus": int,
        "last_3_referrals": [],
        "vip_status": bool,
        "credits_expires_at": "date",
    },

    "Team": {
        "ID": str,
        "UserID": str,
        "Name": str,
        "Role": "array",
        "Email": str,
        "Phone": str,
    },

    "Clips": {"ID": str, "Podcast": int, "ClipName": str},
    "Subscription": {
        "ID": str,
        "user_id": str,
        "last_3_referrals": [],
        "vip_status": bool,
        "credits_expires_at": "date",
    },

    "Team": {"ID": str, "UserID": str, "Name": str, "Role": "array", "Email": str},
    "Clips": {"ID": str, "Podcast": int, "ClipName": str},
    "Subscription": {
        "ID": str,
        "user_id": str,
        "subscription_plan": str,
        "subscription_start": "date",
        "subscription_end": "date",
        "is_active": bool,
    },

    "User": {
        "ID": str,
        "email": str,
        "passwordHash": str,
        "createdAt": "date",
        "partitionKey": str,
        "referral_code": str,
        "referred_by": "string_or_null",
    },

    "Podcast": {
        "ID": str,
        "UserID": str,
        "Podname": str,
        "RSSFeed": str,
        "GoogleCal": "connect",
        "PadURl": str,
        "GuestURL": str,
        "Social_media": "array",
        "Email": str,
    },

    "Podtask": {
        "ID": int,
        "podcast_id": int,
        "Name": str,
        "Action": "array",
        "DayCount": int,
        "Description": str,
        "ActionUrl": str,
        "UrlDescribe": str,
        "SubimissionReq": bool,
    },

}

# Create collections
for collection_name, schema in collections.items():

    if collection_name not in database.list_collection_names():

        database.create_collection(collection_name)
        logger.info(f"Collection '{collection_name}' created successfully.")

    else:
        
        logger.info(f"Collection '{collection_name}' already exists.")
