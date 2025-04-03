from backend.database.mongo_connection import collection

def get_credits_by_user_id(user_id):
    return collection.database.Credits.find_one({"userId": user_id})

def update_credits(user_id, updates):
    return collection.database.Credits.update_one({"userId": user_id}, {"$set": updates})

def increment_credits(user_id, field, amount):
    return collection.database.Credits.update_one({"userId": user_id}, {"$inc": {field: amount}})

def log_credit_transaction(user_id, entry):
    return collection.database.Credits.update_one(
        {"userId": user_id},
        {"$push": {"creditsHistory": entry}}
    )