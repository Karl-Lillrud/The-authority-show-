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
    logger.info(f"Handling successful payment for user_id: {user_id}, session_id: {session.id}")

    # --- Instantiate the Credit Service ---
    credit_service = CreditService() # <-- Create an instance

    amount_paid = session.get('amount_total', 0) / 100

    # Determine credits to add (Keep your existing logic for this)
    metadata = session.get("metadata", {})
    plan = metadata.get("plan", "")
    credits_to_add = int(metadata.get("credits", 0))
    if credits_to_add == 0 and plan:
        credits_to_add = CREDIT_COSTS.get(f"{plan}_pack", 0)
    if credits_to_add == 0 and amount_paid > 0: # Fallback based on amount
        credits_to_add = int(amount_paid * 200) # Example: $1 = 200 credits - Adjust multiplier as needed
        logger.warning(f"Falling back to amount-based credit calculation for user {user_id}: ${amount_paid} -> {credits_to_add} credits")

    if credits_to_add <= 0:
        logger.error(f"No credits determined to add for user {user_id} from session {session.id}. Amount paid: ${amount_paid}")
        # Decide if you want to stop or continue just logging the purchase
        return # Or raise an error?

    logger.info(f"Determined {credits_to_add} credits to add for user {user_id}")

    # --- Ensure Credit Document Exists using CreditService ---
    # Check if user exists, initialize if not. get_user_credits handles this.
    existing_credits = credit_service.get_user_credits(user_id)
    if not existing_credits:
        # Initialization failed within get_user_credits, error already logged.
        logger.error(f"Failed to get or initialize credits for user {user_id}. Aborting credit addition.")
        # Still log the purchase maybe?
        # Log purchase attempt even if credits fail?
        purchase_data = {
            # ... (purchase details) ...
            "status": "Paid - Credit Update Failed",
            "notes": "Failed to find or initialize credit document."
        }
        try:
            collection.database.Purchases.insert_one(purchase_data)
        except Exception as e:
            logger.error(f"Failed to log failed purchase for user {user_id}: {e}")
        return # Stop processing

    # --- Add Credits using CreditService ---
    description = f"Credit purchase (${amount_paid:.2f})"
    add_success = credit_service.add_credits(
        user_id=user_id,
        amount=credits_to_add,
        credit_type="storeCredits", # <-- Add to storeCredits specifically
        description=description
    )

    if not add_success:
        logger.error(f"CreditService failed to add {credits_to_add} storeCredits for user {user_id}.")
        # Log purchase attempt even if credits fail?
        purchase_status = "Paid - Credit Update Failed"
        purchase_notes = f"CreditService.add_credits returned false. Credits added: {credits_to_add}"
    else:
        logger.info(f"Successfully added {credits_to_add} storeCredits for user {user_id} via CreditService.")
        purchase_status = "Paid"
        purchase_notes = None

    # --- Log Purchase ---
    # (Your existing purchase logging logic can stay, but update status/notes if needed)
    purchase_data = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "date": datetime.utcnow(),
        "amount": amount_paid,
        "description": description,
        "status": purchase_status,
        "session_id": session.id,
        "credits_added": credits_to_add, # Good to log this
        "notes": purchase_notes # Add notes if there was an issue
    }

    try:
        collection.database.Purchases.insert_one(purchase_data)
        logger.info(f"Purchase logged for user {user_id}, session {session.id}, status: {purchase_status}")
    except Exception as e:
        logger.error(f"Failed to log purchase entry for user {user_id}: {e}", exc_info=True)