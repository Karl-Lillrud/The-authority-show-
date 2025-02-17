from pymongo import MongoClient
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "podmanagedb"

# Initialize MongoDB Client
client = MongoClient(MONGODB_URI)
database = client[DATABASE_NAME]

# Create collections
collections = {
    "users": database["users"],
    "credits": database["credits"],
    "subscriptions": database["subscriptions"],
    "clips": database["clips"],
    "podcasts": database["podcasts"],
    "teams": database["teams"],
    "podtasks": database["podtasks"],
}

# Clear collections before inserting new documents
for collection in collections.values():
    collection.delete_many({})

# Example documents for collections
example_user = {
    "_id": str(uuid.uuid4()),
    "email": "example@example.com",
    "passwordHash": "hashed_password",
    "createdAt": datetime.utcnow(),
    "referral_code": "REF123",
    "referred_by": None,
}

example_credit = {
    "_id": str(uuid.uuid4()),
    "user_id": example_user["_id"],
    "credits": 100,
    "unclaimed_credits": 50,
    "referral_bonus": 10,
    "referrals": 3,
    "last_3_referrals": [],
    "vip_status": False,
    "credits_expires_at": datetime.utcnow(),
}

example_subscription = {
    "_id": str(uuid.uuid4()),
    "user_id": example_user["_id"],
    "subscription_plan": "basic",
    "subscription_start": datetime.utcnow(),
    "subscription_end": None,
    "is_active": True,
}

example_clip = {
    "_id": 1,
    "Podcast": 1,
    "ClipName": "Sample Clip",
}

example_podcast = {
    "_id": 1,
    "UserID": example_user["_id"],
    "Field1": "Value1",
    "Field2": "Value2",
}

example_team = {
    "_id": 1,
    "UserID": example_user["_id"],
    "Name": "Sample Team",
}

example_podtask = {
    "_id": 1,
    "PodcastID": 1,
    "Field1": "Value1",
    "Field2": "Value2",
}

# Insert example documents into collections
collections["users"].insert_one(example_user)
collections["credits"].insert_one(example_credit)
collections["subscriptions"].insert_one(example_subscription)
collections["clips"].insert_one(example_clip)
collections["podcasts"].insert_one(example_podcast)
collections["teams"].insert_one(example_team)
collections["podtasks"].insert_one(example_podtask)

print("Collections and example documents created successfully.")
