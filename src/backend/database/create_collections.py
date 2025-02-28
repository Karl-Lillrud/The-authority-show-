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
    "Credits": {
        "id": str,
        "availableCredits": int,
        "usedCredits": int,
        "lastUpdated": "date",
        "creditsHistory": "array",
        "creditLimit": int,
    },
    "Teams": {
        "id": str,
        "UserID": str,
        "Name": str,
        "Role": "array",
        "Email": str,
        "Phone": str,
    },
    "Subscriptions": {
        "id": str,
        "subscriptionPlan": str,
        "autoRenew": bool,
        "discountCode": str,
    },
    "Users": {
        "id": str,
        "email": str,
        "passwordHash": str,
        "createdAt": "date",
        "partitionKey": str,
        "referral_code": str,
        "referred_by": "string_or_null",
    },
    "Podcasts": {
        "id": str,
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
    "Podtasks": {
        "id": str,
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
    "Guests": {
        "id": str,
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
    "GuestsToEpisodes": {
        "id": str,
        "episodeId": str,
        "guestId": str,
    },
    "Episodes": {
        "id": str,
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
    "Accounts": {
        "id": str,
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
    "UsersToTeams": {
        "id": str,
        "userId": str,
        "teamId": str,
        "role": str,
        "joinedAt": "date",
    },
}

# Create collections
for collection_name, schema in collections.items():
    if collection_name not in database.list_collection_names():
        database.create_collection(name=collection_name)
        logger.info(f"Collection '{collection_name}' created successfully.")
    else:
        logger.info(f"Collection '{collection_name}' already exists.")

# Ensure indexes to avoid duplicates
for collection_name in collections.keys():
    collection = database[collection_name]
    collection.create_index("id", unique=True)
    logger.info(f"Index on 'id' created for collection '{collection_name}'.")
