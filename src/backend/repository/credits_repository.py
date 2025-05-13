from backend.database.mongo_connection import collection
from datetime import datetime
import uuid

def get_credits_by_user_id(user_id):
    return collection.database.Credits.find_one({"user_id": user_id})

def update_credits(user_id, updates):
    return collection.database.Credits.update_one({"user_id": user_id}, {"$set": updates})

def increment_credits(user_id, field, amount):
    return collection.database.Credits.update_one({"user_id": user_id}, {"$inc": {field: amount}})

def log_credit_transaction(user_id, entry):
  
    if "_id" not in entry:
        entry["_id"] = str(uuid.uuid4())
    
    # Ensure timestamp is a datetime
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.utcnow()
        
    return collection.database.Credits.update_one(
        {"user_id": user_id},
        {"$push": {"creditsHistory": entry}}
    )

def delete_by_user(user_id):
    return collection.database.Credits.delete_one({"user_id": user_id})