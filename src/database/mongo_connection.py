from pymongo import MongoClient
from flask import Blueprint
import os
from dotenv import load_dotenv
import logging

mongo_bp = Blueprint("mongo_bp", __name__)

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"

if not MONGODB_URI:
    raise ValueError("❌ MongoDB URI saknas. Kontrollera din .env-fil.")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB Client
try:
    client = MongoClient(MONGODB_URI)
    database = client[DATABASE_NAME]

    # 📌 Definiera collections
    users_collection = database["users"]
    credits_collection = database["credits"]

    logger.info("✅ MongoDB-anslutning upprättad.")

    # 📌 Kontrollera om `credits_collection` finns
    existing_collections = database.list_collection_names()
    if "credits" not in existing_collections:
        logger.warning("⚠️ Credits-collection saknas. Skapar ett testdokument för att initiera den...")
        credits_collection.insert_one({
            "user_id": "init_test",
            "credits": 0,
            "unclaimed_credits": 0,
            "referral_bonus": 0,
            "referrals": 0,
            "last_3_referrals": [],
            "vip_status": False,
            "credits_expires_at": "N/A"
        })
        logger.info("✅ Credits-collection skapad.")

except Exception as e:
    logger.error(f"❌ Misslyckades att ansluta till MongoDB: {e}")
    raise
