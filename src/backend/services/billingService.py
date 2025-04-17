# backend/services/billingService.py
from datetime import datetime
from backend.repository.credits_repository import get_credits_by_user_id, update_credits
from backend.services.creditService import initialize_credits  # Add this import

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
