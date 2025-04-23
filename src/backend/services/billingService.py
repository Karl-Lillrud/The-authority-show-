from datetime import datetime
import uuid
from backend.repository.credits_repository import get_credits_by_user_id, update_credits, log_credit_transaction
from backend.services.creditService import initialize_credits
from backend.database.mongo_connection import collection
from backend.utils.credit_costs import CREDIT_COSTS

def handle_successful_payment(session, user_id):
    amount_paid = session['amount_total'] / 100

    # 🧠 Prefer metadata-provided credits (from frontend/session creation)
    metadata = session.get("metadata", {})
    plan = metadata.get("plan", "")
    credits_to_add = int(metadata.get("credits", 0))

    # 🛡 Fallback: use credit_costs.py plan mapping
    if credits_to_add == 0 and plan:
        credits_to_add = CREDIT_COSTS.get(f"{plan}_pack", 0)

    # 🧯 Final fallback: default multiplier
    if credits_to_add == 0:
        credits_to_add = int(amount_paid * 1000)

    # 🔄 Credit account management
    existing = get_credits_by_user_id(user_id)
    if not existing:
        initialize_credits(user_id)
        existing = get_credits_by_user_id(user_id)
        if not existing:
            raise ValueError("Failed to create credits account for this user.")

    updated = {
        "availableCredits": existing["availableCredits"] + credits_to_add,
        "lastUpdated": datetime.utcnow()
    }
    update_credits(user_id, updated)

    # 🧾 Purchase log
    purchase_data = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "date": datetime.utcnow(),
        "amount": amount_paid,
        "description": f"Credit purchase ({credits_to_add} credits)",
        "status": "Paid",
        "session_id": session.id
    }

    # 🪙 Credit transaction log
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
