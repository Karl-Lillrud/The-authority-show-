from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

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
        "subscription_plan": str,
        "subscription_start": "date",
        "subscription_end": "date",
        "last_3_referrals": [],
        "vip_status": bool,
        "credits_expires_at": "date",
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
        "ID": int,  # Om du vill ha ett numeriskt ID, annars kan du använda str
        "podcast_id": str,  # Om PodcastId kommer som str (annars använd int)
        "Name": str,
        "Action": "array",  # Här kan du ange "array" eller list om du vill dokumentera
        "DayCount": int,
        "Description": str,
        "ActionUrl": str,
        "UrlDescribe": str,
        "SubimissionReq": bool,
    },
    "Guest": {
        "ID": str,
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
        "created_at": "date",
    },
}

# Create collections
for collection_name, schema in collections.items():
    if collection_name not in database.list_collection_names():
        database.create_collection(collection_name)
        logger.info(f"Collection '{collection_name}' created successfully.")
    else:
        logger.info(f"Collection '{collection_name}' already exists.")

# Example data for each collection
example_data = {
    "users": [
        {
            "id": "1",
            "email": "user1@example.com",
            "passwordHash": "hash1",
            "createdAt": datetime.utcnow(),
            "referralCode": "code1",
            "referredBy": None,
        },
        {
            "id": "2",
            "email": "user2@example.com",
            "passwordHash": "hash2",
            "createdAt": datetime.utcnow(),
            "referralCode": "code2",
            "referredBy": "1",
        },
        {
            "id": "3",
            "email": "user3@example.com",
            "passwordHash": "hash3",
            "createdAt": datetime.utcnow(),
            "referralCode": "code3",
            "referredBy": "1",
        },
    ],
    "users_to_teams": [
        {
            "id": "1",
            "userId": "1",
            "teamId": "1",
            "role": "admin",
            "assignedAt": datetime.utcnow(),
        },
        {
            "id": "2",
            "userId": "2",
            "teamId": "1",
            "role": "member",
            "assignedAt": datetime.utcnow(),
        },
        {
            "id": "3",
            "userId": "3",
            "teamId": "2",
            "role": "member",
            "assignedAt": datetime.utcnow(),
        },
    ],
    "teams": [
        {
            "id": "1",
            "name": "Team A",
            "email": "teamA@example.com",
            "description": "Description A",
            "isActive": True,
            "joinedAt": datetime.utcnow(),
            "lastActive": datetime.utcnow(),
            "members": [],
        },
        {
            "id": "2",
            "name": "Team B",
            "email": "teamB@example.com",
            "description": "Description B",
            "isActive": True,
            "joinedAt": datetime.utcnow(),
            "lastActive": datetime.utcnow(),
            "members": [],
        },
        {
            "id": "3",
            "name": "Team C",
            "email": "teamC@example.com",
            "description": "Description C",
            "isActive": True,
            "joinedAt": datetime.utcnow(),
            "lastActive": datetime.utcnow(),
            "members": [],
        },
    ],
    "subscriptions": [
        {
            "id": "1",
            "subscriptionPlan": "Basic",
            "autoRenew": True,
            "discountCode": "DISCOUNT1",
        },
        {
            "id": "2",
            "subscriptionPlan": "Pro",
            "autoRenew": False,
            "discountCode": "DISCOUNT2",
        },
        {
            "id": "3",
            "subscriptionPlan": "Premium",
            "autoRenew": True,
            "discountCode": "DISCOUNT3",
        },
    ],
    "podtasks": [
        {
            "id": "1",
            "podcastId": "1",
            "name": "Task 1",
            "action": ["action1"],
            "dayCount": 1,
            "description": "Description 1",
            "actionUrl": "http://example.com",
            "urlDescribe": "URL 1",
            "submissionReq": True,
            "status": "pending",
            "assignedAt": datetime.utcnow(),
            "dueDate": datetime.utcnow(),
            "priority": "high",
        },
        {
            "id": "2",
            "podcastId": "2",
            "name": "Task 2",
            "action": ["action2"],
            "dayCount": 2,
            "description": "Description 2",
            "actionUrl": "http://example.com",
            "urlDescribe": "URL 2",
            "submissionReq": True,
            "status": "pending",
            "assignedAt": datetime.utcnow(),
            "dueDate": datetime.utcnow(),
            "priority": "medium",
        },
        {
            "id": "3",
            "podcastId": "3",
            "name": "Task 3",
            "action": ["action3"],
            "dayCount": 3,
            "description": "Description 3",
            "actionUrl": "http://example.com",
            "urlDescribe": "URL 3",
            "submissionReq": True,
            "status": "pending",
            "assignedAt": datetime.utcnow(),
            "dueDate": datetime.utcnow(),
            "priority": "low",
        },
    ],
    "podcasts": [
        {
            "id": "1",
            "teamId": "1",
            "accountId": "1",
            "podName": "Podcast 1",
            "ownerName": "Owner 1",
            "hostName": "Host 1",
            "rssFeed": "http://rss1.com",
            "googleCal": "cal1",
            "guestUrl": "guest1",
            "socialMedia": ["twitter1"],
            "email": "podcast1@example.com",
            "description": "Description 1",
            "logoUrl": "http://logo1.com",
            "category": "Category 1",
            "podUrl": "http://pod1.com",
        },
        {
            "id": "2",
            "teamId": "2",
            "accountId": "2",
            "podName": "Podcast 2",
            "ownerName": "Owner 2",
            "hostName": "Host 2",
            "rssFeed": "http://rss2.com",
            "googleCal": "cal2",
            "guestUrl": "guest2",
            "socialMedia": ["twitter2"],
            "email": "podcast2@example.com",
            "description": "Description 2",
            "logoUrl": "http://logo2.com",
            "category": "Category 2",
            "podUrl": "http://pod2.com",
        },
        {
            "id": "3",
            "teamId": "3",
            "accountId": "3",
            "podName": "Podcast 3",
            "ownerName": "Owner 3",
            "hostName": "Host 3",
            "rssFeed": "http://rss3.com",
            "googleCal": "cal3",
            "guestUrl": "guest3",
            "socialMedia": ["twitter3"],
            "email": "podcast3@example.com",
            "description": "Description 3",
            "logoUrl": "http://logo3.com",
            "category": "Category 3",
            "podUrl": "http://pod3.com",
        },
    ],
    "guests": [
        {
            "id": "1",
            "podcastId": "1",
            "name": "Guest 1",
            "image": "http://image1.com",
            "tags": ["tag1"],
            "description": "Description 1",
            "bio": "Bio 1",
            "email": "guest1@example.com",
            "linkedin": "http://linkedin1.com",
            "twitter": "http://twitter1.com",
            "areasOfInterest": ["interest1"],
            "status": "confirmed",
            "scheduled": 1,
            "completed": 1,
            "createdAt": datetime.utcnow(),
            "notes": "Notes 1",
        },
        {
            "id": "2",
            "podcastId": "2",
            "name": "Guest 2",
            "image": "http://image2.com",
            "tags": ["tag2"],
            "description": "Description 2",
            "bio": "Bio 2",
            "email": "guest2@example.com",
            "linkedin": "http://linkedin2.com",
            "twitter": "http://twitter2.com",
            "areasOfInterest": ["interest2"],
            "status": "confirmed",
            "scheduled": 2,
            "completed": 2,
            "createdAt": datetime.utcnow(),
            "notes": "Notes 2",
        },
        {
            "id": "3",
            "podcastId": "3",
            "name": "Guest 3",
            "image": "http://image3.com",
            "tags": ["tag3"],
            "description": "Description 3",
            "bio": "Bio 3",
            "email": "guest3@example.com",
            "linkedin": "http://linkedin3.com",
            "twitter": "http://twitter3.com",
            "areasOfInterest": ["interest3"],
            "status": "confirmed",
            "scheduled": 3,
            "completed": 3,
            "createdAt": datetime.utcnow(),
            "notes": "Notes 3",
        },
    ],
    "edits": [
        {
            "id": "1",
            "podcastId": "1",
            "clipName": "Clip 1",
            "duration": 60,
            "createdAt": datetime.utcnow(),
            "editedBy": ["editor1"],
            "clipUrl": "http://clip1.com",
            "status": "completed",
            "tags": ["tag1"],
        },
        {
            "id": "2",
            "podcastId": "2",
            "clipName": "Clip 2",
            "duration": 120,
            "createdAt": datetime.utcnow(),
            "editedBy": ["editor2"],
            "clipUrl": "http://clip2.com",
            "status": "completed",
            "tags": ["tag2"],
        },
        {
            "id": "3",
            "podcastId": "3",
            "clipName": "Clip 3",
            "duration": 180,
            "createdAt": datetime.utcnow(),
            "editedBy": ["editor3"],
            "clipUrl": "http://clip3.com",
            "status": "completed",
            "tags": ["tag3"],
        },
    ],
    "credits": [
        {
            "id": "1",
            "availableCredits": 100,
            "usedCredits": 10,
            "lastUpdated": datetime.utcnow(),
            "creditsHistory": [{"action": "add", "amount": 100}],
            "creditLimit": 200,
        },
        {
            "id": "2",
            "availableCredits": 200,
            "usedCredits": 20,
            "lastUpdated": datetime.utcnow(),
            "creditsHistory": [{"action": "add", "amount": 200}],
            "creditLimit": 300,
        },
        {
            "id": "3",
            "availableCredits": 300,
            "usedCredits": 30,
            "lastUpdated": datetime.utcnow(),
            "creditsHistory": [{"action": "add", "amount": 300}],
            "creditLimit": 400,
        },
    ],
    "accounts": [
        {
            "id": "1",
            "ownerId": "1",
            "subscriptionId": "1",
            "creditId": "1",
            "email": "account1@example.com",
            "isCompany": True,
            "companyName": "Company 1",
            "paymentInfo": "Payment 1",
            "subscriptionStatus": "active",
            "createdAt": datetime.utcnow(),
            "referralBonus": 10,
            "subscriptionStart": datetime.utcnow(),
            "subscriptionEnd": datetime.utcnow(),
            "isActive": True,
        },
        {
            "id": "2",
            "ownerId": "2",
            "subscriptionId": "2",
            "creditId": "2",
            "email": "account2@example.com",
            "isCompany": True,
            "companyName": "Company 2",
            "paymentInfo": "Payment 2",
            "subscriptionStatus": "active",
            "createdAt": datetime.utcnow(),
            "referralBonus": 20,
            "subscriptionStart": datetime.utcnow(),
            "subscriptionEnd": datetime.utcnow(),
            "isActive": True,
        },
        {
            "id": "3",
            "ownerId": "3",
            "subscriptionId": "3",
            "creditId": "3",
            "email": "account3@example.com",
            "isCompany": True,
            "companyName": "Company 3",
            "paymentInfo": "Payment 3",
            "subscriptionStatus": "active",
            "createdAt": datetime.utcnow(),
            "referralBonus": 30,
            "subscriptionStart": datetime.utcnow(),
            "subscriptionEnd": datetime.utcnow(),
            "isActive": True,
        },
    ],
    "episodes": [
        {
            "id": "1",
            "podcastId": "1",
            "title": "Episode 1",
            "description": "Description 1",
            "duration": 60,
            "releaseDate": datetime.utcnow(),
            "status": "published",
        },
        {
            "id": "2",
            "podcastId": "2",
            "title": "Episode 2",
            "description": "Description 2",
            "duration": 120,
            "releaseDate": datetime.utcnow(),
            "status": "published",
        },
        {
            "id": "3",
            "podcastId": "3",
            "title": "Episode 3",
            "description": "Description 3",
            "duration": 180,
            "releaseDate": datetime.utcnow(),
            "status": "published",
        },
    ],
}

# Create collections and insert example data
for collection_name, documents in example_data.items():
    collection = database[collection_name]
    collection.insert_many(documents)

print("Collections created and example documents inserted.")
