from datetime import datetime
from database.mongo_connection import collection
from backend.utils.credit_costs import CREDIT_COSTS
from backend.repository.credits_repository import (
    get_credits_by_user_id, update_credits, log_credit_transaction
)

def get_user_credits(user_id):
    return get_credits_by_user_id(user_id)

def consume_credits(user_id, feature_name):
    cost = CREDIT_COSTS.get(feature_name)
    if cost is None:
        raise ValueError("Invalid feature name.")

    credits = get_credits_by_user_id(user_id)
    if not credits:
        raise ValueError("No credits account found for user.")

    available = credits.get("availableCredits", 0)
    if available < cost:
        raise ValueError("Insufficient credits.")

    new_available = available - cost
    new_used = credits.get("usedCredits", 0) + cost

    update_credits(user_id, {
        "availableCredits": new_available,
        "usedCredits": new_used,
        "lastUpdated": datetime.utcnow()
    })

    log_credit_transaction(user_id, {
        "feature": feature_name,
        "cost": cost,
        "timestamp": datetime.utcnow()
    })

    return {"remaining": new_available, "used": new_used}

def initialize_credits(user_id: str, initial_amount=3000):
    collection.database.Credits.insert_one({
        "user_id": user_id,
        "availableCredits": initial_amount,
        "usedCredits": 0,
        "creditLimit": initial_amount,
        "lastUpdated": datetime.utcnow(),
        "creditsHistory": []
    })