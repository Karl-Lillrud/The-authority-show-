# File: backend/services/billingService.py
import logging
from datetime import datetime
import uuid

from backend.services.creditManagement import CreditService
from backend.database.mongo_connection import collection
from backend.utils.credit_costs import CREDIT_COSTS

logger = logging.getLogger(__name__)


def handle_successful_payment(session, user_id):
    """
    Handles logic after a successful Stripe payment.
    Updates user credits using the CreditService.
    """
    logger.info(
        f"Handling successful payment for user_id: {user_id}, session_id: {session.id}"
    )

    # --- Instantiate the Credit Service ---
    credit_service = CreditService()

    amount_paid = session.get("amount_total", 0) / 100

    # Determine credits to add
    metadata = session.get("metadata", {})
    plan = metadata.get("plan", "")
    credits_to_add = int(metadata.get("credits", 0))

    # If no credits specified in metadata, check if it's a credits-only purchase
    if credits_to_add == 0 and not plan:
        # Map amount to credits based on credit pack pricing
        credit_pack_mapping = {
            7.99: 2500,  # Basic Pack
            14.99: 5000,  # Pro Pack
            29.99: 12000,  # Studio Pack
        }
        credits_to_add = credit_pack_mapping.get(amount_paid, 0)
        if credits_to_add == 0:
            credits_to_add = int(amount_paid * 200)  # Fallback: $1 = 200 credits
            logger.warning(
                f"Falling back to amount-based credit calculation for user {user_id}: ${amount_paid} -> {credits_to_add} credits"
            )

    if credits_to_add <= 0:
        logger.error(
            f"No credits determined to add for user {user_id} from session {session.id}. Amount paid: ${amount_paid}"
        )
        return

    logger.info(f"Determined {credits_to_add} credits to add for user {user_id}")

    # --- Ensure Credit Document Exists using CreditService ---
    existing_credits = credit_service.get_user_credits(user_id)
    if not existing_credits:
        # Initialize credits if not found
        credit_service.initialize_credits(user_id, initial_user=credits_to_add)
        logger.info(
            f"Initialized credits for user {user_id} with {credits_to_add} storeCredits"
        )
    else:
        # Add credits to storeCredits
        description = f"Credit purchase (${amount_paid:.2f})"
        add_success = credit_service.add_credits(
            user_id=user_id,
            amount=credits_to_add,
            credit_type="storeCredits",  # Fixed typo from 'credit' to 'credit_type'
            description=description,
        )

        if not add_success:
            logger.error(
                f"CreditService failed to add {credits_to_add} storeCredits for user {user_id}."
            )
            purchase_status = "Paid - Credit Update Failed"
            purchase_notes = f"CreditService.add_credits returned false. Credits added: {credits_to_add}"
        else:
            logger.info(
                f"Successfully added {credits_to_add} storeCredits for user {user_id} via CreditService."
            )
            purchase_status = "Paid"
            purchase_notes = None

    # --- Log Purchase ---
    purchase_data = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "date": datetime.utcnow(),
        "amount": amount_paid,
        "description": f"Credit purchase (${amount_paid:.2f})",
        "status": purchase_status if "purchase_status" in locals() else "Paid",
        "session_id": session.id,
        "credits_added": credits_to_add,
        "notes": purchase_notes if "purchase_notes" in locals() else None,
    }

    try:
        collection.database.Purchases.insert_one(purchase_data)
        logger.info(
            f"Purchase logged for user {user_id}, session {session.id}, status: {purchase_data['status']}"
        )
    except Exception as e:
        logger.error(
            f"Failed to log purchase entry for user {user_id}: {e}", exc_info=True
        )
