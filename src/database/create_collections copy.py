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


def create_collections():
    collections = {
        "users_to_teams": [{"id": "1", "userId": "user1", "teamId": "team1"}],
        "teams": [
            {
                "id": "1",
                "name": "Team A",
                "role": "owner",
                "email": "team@example.com",
                "phone": "1234567890",
                "isActive": True,
                "joinedAt": "2023-01-01",
                "lastActive": "2023-01-02",
            }
        ],
        "subscriptions": [
            {
                "id": "1",
                "subscriptionPlan": "Basic",
                "autoRenew": True,
                "discountCode": "DISCOUNT2023",
            }
        ],
        "podtasks": [
            {
                "id": "1",
                "podcastId": "podcast1",
                "name": "Task 1",
                "action": "action1",
                "dayCount": 5,
                "description": "Description 1",
                "actionUrl": "http://example.com",
                "urlDescribe": "URL Description",
                "submissionReq": True,
                "status": "Pending",
                "assignedAt": "2023-01-01",
                "dueDate": "2023-01-10",
                "priority": "High",
            }
        ],
        "podcasts": [
            {
                "id": "1",
                "teamId": "team1",
                "accountId": "account1",
                "podName": "Podcast 1",
                "ownerName": "Owner 1",
                "hostName": "Host 1",
                "rssFeed": "http://rssfeed.com",
                "googleCal": "http://googlecal.com",
                "podUrl": "http://podurl.com",
                "guestUrl": "http://guesturl.com",
                "socialMedia": "http://socialmedia.com",
                "email": "podcast@example.com",
                "description": "Description 1",
                "logoUrl": "http://logourl.com",
                "category": "Category 1",
                "defaultTasks": "Task 1",
            }
        ],
        "guests": [
            {
                "id": "1",
                "podcastId": "podcast1",
                "name": "Guest 1",
                "image": "http://image.com",
                "tags": "tag1",
                "description": "Description 1",
                "bio": "Bio 1",
                "email": "guest@example.com",
                "linkedin": "http://linkedin.com",
                "twitter": "http://twitter.com",
                "areasOfInterest": "Interest 1",
                "status": "Active",
                "scheduled": 1,
                "completed": 1,
                "createdAt": "2023-01-01",
                "notes": "Notes 1",
            }
        ],
        "episodes": [
            {
                "id": "1",
                "guestId": "guest1",
                "podcastId": "podcast1",
                "title": "Episode 1",
                "description": "Description 1",
                "publishDate": "2023-01-01",
                "duration": 60,
                "status": "Published",
                "createdAt": "2023-01-01",
                "updatedAt": "2023-01-02",
            }
        ],
        "clips": [
            {
                "id": "1",
                "podcastId": "podcast1",
                "clipName": "Clip 1",
                "duration": 30,
                "createdAt": "2023-01-01",
                "editedBy": "editor1",
                "clipUrl": "http://clipurl.com",
                "status": "Completed",
                "tags": "tag1",
            }
        ],
        "credits": [
            {
                "id": "1",
                "availableCredits": 100,
                "usedCredits": 50,
                "lastUpdated": "2023-01-01",
                "creditsHistory": "History 1",
                "creditLimit": 200,
            }
        ],
        "accounts": [
            {
                "id": "1",
                "ownerId": "owner1",
                "subscriptionId": "subscription1",
                "creditId": "credit1",
                "email": "account@example.com",
                "isCompany": True,
                "companyName": "Company 1",
                "paymentInfo": "Payment Info",
                "subscriptionStatus": "Active",
                "createdAt": "2023-01-01",
                "referralBonus": 10,
                "subscriptionStart": "2023-01-01",
                "subscriptionEnd": "2023-12-31",
                "isActive": True,
            }
        ],
        "users": [
            {
                "id": "1",
                "name": "User 1",
                "email": "user1@example.com",
                "passwordHash": "hashed_password",
                "createdAt": "2023-01-01",
                "referralCode": "REF123",
                "referredBy": None,
            }
        ],
    }

    for collection_name, documents in collections.items():
        collection = database[collection_name]
        collection.insert_many(documents)
        logger.info(f"Inserted documents into {collection_name} collection.")


if __name__ == "__main__":
    create_collections()
