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
    "credits": {
        "ID": str,
        "availableCredits": int,
        "usedCredits": int,
        "lastUpdated": "date",
        "creditsHistory": "array",
        "creditLimit": int,
    },
    "teams": {
        "ID": str,
        "UserID": str,
        "Name": str,
        "Role": "array",
        "Email": str,
        "Phone": str,
    },
    "clips": {
        "ID": str,
        "podcastId": str,
        "clipName": str,
        "duration": int,
        "createdAt": "date",
        "editedBy": "array",
        "clipUrl": str,
        "status": str,
        "tags": "array",
    },
    "subscriptions": {
        "ID": str,
        "subscriptionPlan": str,
        "autoRenew": bool,
        "discountCode": str,
    },
    "users": {
        "ID": str,
        "email": str,
        "passwordHash": str,
        "createdAt": "date",
        "partitionKey": str,
        "referral_code": str,
        "referred_by": "string_or_null",
    },
    "podcasts": {
        "ID": str,
        "teamId": str,
        "accountId": str,
        "podName": str,
        "ownerName": str,
        "hostName": str,
        "rssFeed": str,
        "googleCal": str,
        "guestUrl": str,
        "socialMedia": "array",
        "email": str,
        "description": str,
        "logoUrl": str,
        "category": str,
        "podUrl": str,
    },
    "podtasks": {
        "ID": str,
        "podcastId": str,
        "name": str,
        "action": "array",
        "dayCount": int,
        "description": str,
        "actionUrl": str,
        "urlDescribe": str,
        "submissionReq": bool,
        "status": str,
        "assignedAt": "date",
        "dueDate": "date",
        "priority": str,
    },
    "guests": {
        "ID": str,
        "podcastId": str,
        "name": str,
        "image": str,
        "tags": "array",
        "description": str,
        "bio": str,
        "email": str,
        "linkedin": str,
        "twitter": str,
        "areasOfInterest": "array",
        "status": str,
        "scheduled": int,
        "completed": int,
        "createdAt": "date",
        "notes": str,
    },
    "guests_to_episodes": {
        "ID": str,
        "episodeId": str,
        "guestId": str,
    },
    "episodes": {
        "ID": str,
        "guestId": str,
        "podcastId": str,
        "title": str,
        "description": str,
        "publishDate": "date",
        "duration": int,
        "status": str,
        "createdAt": "date",
        "updatedAt": "date",
    },
    "accounts": {
        "ID": str,
        "ownerId": str,
        "subscriptionId": str,
        "creditId": str,
        "email": str,
        "isCompany": bool,
        "companyName": str,
        "paymentInfo": str,
        "subscriptionStatus": str,
        "createdAt": "date",
        "referralBonus": int,
        "subscriptionStart": "date",
        "subscriptionEnd": "date",
        "isActive": bool,
    },
    "users_to_teams": {
        "ID": str,
        "userId": str,
        "teamId": str,
        "role": str,
        "joinedAt": "date",
    },
}

# Create collections
for collection_name, schema in collections.items():
    if collection_name not in database.list_collection_names():
        database.create_collection(collection_name)
        logger.info(f"Collection '{collection_name}' created successfully.")
    else:
        logger.info(f"Collection '{collection_name}' already exists.")

# Ensure indexes to avoid duplicates
for collection_name in collections.keys():
    collection = database[collection_name]
    collection.create_index("ID", unique=True)
    logger.info(f"Index on 'ID' created for collection '{collection_name}'.")
