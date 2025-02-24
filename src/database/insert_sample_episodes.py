from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timezone

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


def insert_sample_episodes():
    episodes = [
        {
            "id": "EPISODE_ID_1",
            "guestId": "GUEST_ID_1",
            "podcastId": "podcast1",
            "title": "Episode 1",
            "description": "Description 1",
            "publishDate": "2023-01-01",
            "duration": 60,
            "status": "Published",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": "EPISODE_ID_2",
            "guestId": "GUEST_ID_2",
            "podcastId": "podcast1",
            "title": "Episode 2",
            "description": "Description 2",
            "publishDate": "2023-01-02",
            "duration": 45,
            "status": "Published",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": "EPISODE_ID_3",
            "guestId": "GUEST_ID_3",
            "podcastId": "podcast1",
            "title": "Episode 3",
            "description": "Description 3",
            "publishDate": "2023-01-03",
            "duration": 30,
            "status": "Published",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    ]

    collection = database["episodes"]
    collection.insert_many(episodes)
    logger.info("Inserted sample episodes into the episodes collection.")


if __name__ == "__main__":
    insert_sample_episodes()
