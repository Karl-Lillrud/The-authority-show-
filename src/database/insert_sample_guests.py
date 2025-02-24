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


def insert_sample_guests():
    guests = [
        {
            "id": "GUEST_ID_1",
            "name": "Ollina Olsson",
            "image": "https://podmanagerstorage.blob.core.windows.net/blob-container/person1.jpg",
            "description": "Guest A Description",
            "email": "ollina@example.com",
        },
        {
            "id": "GUEST_ID_2",
            "name": "Olle Olsson",
            "image": "https://podmanagerstorage.blob.core.windows.net/blob-container/person2.jpg",
            "description": "Guest B Description",
            "email": "olle@example.com",
        },
        {
            "id": "GUEST_ID_3",
            "name": "Olga Olsson",
            "image": "https://podmanagerstorage.blob.core.windows.net/blob-container/person3.jpg",
            "description": "Guest C Description",
            "email": "olga@example.com",
        },
    ]

    collection = database["guests"]
    collection.insert_many(guests)
    logger.info("Inserted sample guests into the guests collection.")


if __name__ == "__main__":
    insert_sample_guests()
