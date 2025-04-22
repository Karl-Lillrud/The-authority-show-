# backend/services/billingService.py
from datetime import datetime
import uuid
from backend.repository.credits_repository import get_credits_by_user_id, update_credits, log_credit_transaction
from backend.services.creditService import initialize_credits
from backend.database.mongo_connection import collection

def handle_successful_payment(session, user_id):
    amount_paid = session['amount_total'] / 100
    credits_to_add = int(amount_paid * 1000)

    existing = get_credits_by_user_id(user_id)
    if not existing:
        # Create credits account if it doesn't exist
        initialize_credits(user_id)
        existing = get_credits_by_user_id(user_id)
        if not existing:
            raise ValueError("Failed to create credits account for this user.")

    updated = {
        "availableCredits": existing["availableCredits"] + credits_to_add,
        "lastUpdated": datetime.utcnow()
    }
    update_credits(user_id, updated)
    
    # Log the purchase to the database with string ID
    purchase_data = {
        "_id": str(uuid.uuid4()),  # Use string UUID instead of auto-generated ObjectId
        "user_id": user_id,
        "date": datetime.utcnow(),
        "amount": amount_paid,
        "description": f"Credit purchase ({credits_to_add} credits)",
        "status": "Paid",
        "session_id": session.id
    }
    
    # Also add to credits history
    credit_entry = {
        "_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow(),
        "amount": credits_to_add,
        "type": "purchase",
        "description": f"Credit purchase (${amount_paid})",
        "status": "completed"
    }
    log_credit_transaction(user_id, credit_entry)
    
    collection.database.Purchases.insert_one(purchase_data)
