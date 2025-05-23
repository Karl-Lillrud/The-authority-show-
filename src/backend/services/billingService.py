# File: backend/services/billingService.py
import logging
from datetime import datetime
import uuid

from backend.services.creditManagement import CreditService
from backend.database.mongo_connection import collection
from backend.repository.account_repository import AccountRepository
from backend.utils.credit_costs import CREDIT_COSTS

logger = logging.getLogger(__name__)


def handle_successful_payment(session, user_id):
    """
    Handles logic after a successful Stripe payment.
    Updates user credits using the CreditService and logs purchase details.
    """
    logger.info(
        f"Handling successful payment for user_id: {user_id}, session_id: {session.id}"
    )

    # --- Instantiate the Credit Service ---
    credit_service = CreditService()

    amount_paid = session.get("amount_total", 0) / 100

    # Extract product details from session line_items
    details = []
    line_items = session.get("line_items", {}).get(
        "data", []
    )  # Safely access line_items.data
    if not line_items:
        logger.warning(
            f"No line_items found in session {session.id} for user {user_id}"
        )

    for item in line_items:
        product_name = item.get("description", "Unknown Product")
        quantity = item.get("quantity", 1)
        price = item.get("amount_total", 0) / 100  # Convert cents to dollars
        details.append({"product": product_name, "quantity": quantity, "price": price})

    metadata = session.get("metadata", {})
    plan = metadata.get("plan", "")
    credits_to_add = int(metadata.get("credits", 0))
    extra_episodes_unlock = int(metadata.get("episode_slots", 0))
    
    # If no credits specified in metadata and no plan, fallback to credit pack mapping
    if credits_to_add == 0 and not plan and extra_episodes_unlock == 0:
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

    if credits_to_add <= 0 and not plan and extra_episodes_unlock <= 0:
        logger.error(
            f"No credits determined to add for user {user_id} from session {session.id}. Amount paid: ${amount_paid}"
        )
        return

    # Generate a descriptive description based on purchased items
    description_parts = []
    if plan:
        description_parts.append(f"{plan.capitalize()} Subscription")
    if extra_episodes_unlock > 0:
        description_parts.append(f"Extra Episode Pack: ({extra_episodes_unlock}) slots")
    if credits_to_add > 0:
        description_parts.append(f"Credit Pack ({credits_to_add} credits)")
    description = f"Purchase: {', '.join(description_parts)} (${amount_paid:.2f})"

    if credits_to_add > 0:
        # --- Ensure Credit Document Exists using CreditService ---
        existing_credits = credit_service.get_store_credits(user_id)  # Updated method name
        if not existing_credits:
            # Initialize credits if not found
            credit_service.initialize_credits(user_id, initial_user=credits_to_add)
            logger.info(
                f"Initialized credits for user {user_id} with {credits_to_add} storeCredits"
            )
        else:
            # Add credits to storeCredits if applicable
            if credits_to_add > 0:
                credit_description = f"Credit purchase (${amount_paid:.2f})"
                add_success = credit_service.add_credits(
                    user_id=user_id,
                    amount=credits_to_add,
                    credit_type="storeCredits",
                    description=credit_description,
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
            else:
                purchase_status = "Paid"
                purchase_notes = None

    if extra_episodes_unlock > 0:
        # --- Unlock Episodes Logic ---
        print("Unlocking episodes...")
        try:
            update_query = {"ownerId": user_id}
            
            update_result = collection.database.Accounts.update_one(
                update_query,
                {
                    "$inc": {
                        "unlockedExtraEpisodeSlots": extra_episodes_unlock,
                    }
                },
            )
            logger.info(f"Account update result: matched={update_result.matched_count}, modified={update_result.modified_count}")   

            if update_result.modified_count == 0:
                logger.error(f"Failed to update unlockedExtraEpisodeSlots - no document matched")
                purchase_status = "Paid - Episode Unlock Failed"    
                purchase_notes = "Failed to update unlockedExtraEpisodeSlots in database." 
            else:
                logger.info(f"Successfully unlocked {extra_episodes_unlock} episodes for user {user_id}.")
                purchase_status = "Paid"
        except Exception as e:
            logger.error(
                f"Error unlocking episodes for user {user_id}: {e}", exc_info=True
            )
            purchase_status = "Paid - Episode Unlock Error"
            purchase_notes = str(e) 



    # --- Log Purchase ---
    purchase_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "date": datetime.utcnow(),
        "amount": amount_paid,
        "description": description,
        "details": details,
        "status": purchase_status if "purchase_status" in locals() else "Paid",
        "session_id": session.id,
        "credits_added": credits_to_add if credits_to_add > 0 else 0,
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

def update_subscription_status(user_id, status):
    """
    Update the subscription status for a user.
    """
    logger.info(f"Updating subscription status for user {user_id} to {status}")

    # Determine the field name based on the Accounts collection schema
    account_field = "userId"  # Default to userId
    subscription_field = "user_id"  # Default to user_id

    # 1. Find the account by userId or ownerId
    account = collection.database.Accounts.find_one({
        "$or": [{"userId": user_id}, {"ownerId": user_id}]
    })

    if account:
        # If account found, update the subscription status
        logger.info(f"Account found for user {user_id}, updating subscription status")
        
        # Update subscription status in Accounts collection
        collection.database.Accounts.update_one(
            {"id": account["id"]},  # Use account's own id
            {
                "$set": {
                    "subscriptionStatus": status,
                }
            }
        )

        # Also update in Subscriptions collection
        collection.database.Subscriptions.update_one(
            {"user_id": user_id, "status": "active"},
            {
                "$set": {
                    "status": status,
                }
            }
        )

        logger.info(f"Subscription status updated to {status} for user {user_id}")
    else:
        logger.warning(f"No account found for user {user_id} to update subscription status")

def handle_stripe_webhook(event):
    """
    Handle incoming Stripe webhook events.
    """
    logger.info(f"Received Stripe webhook: {event['type']}")

    # Extract relevant data from the event
    event_type = event["type"]
    data_object = event["data"].get("object", {})

    # Handle different event types
    if event_type == "customer.subscription.updated":
        # Subscription updated
        logger.info("Subscription updated event received")
        subscription = data_object
        customer_id = subscription.get("customer")
        status = subscription.get("status")
        plan_name = subscription.get("plan", {}).get("nickname", "No Plan Name")

        # 1. Find the associated user account
        account = collection.database.Accounts.find_one({
            "$or": [{"stripeCustomerId": customer_id}, {"userId": customer_id}, {"ownerId": customer_id}]
        })

        if account:
            user_id_val = account.get("userId") or account.get("ownerId") # Renamed user_id to user_id_val
            
            # Check if this is an upgrade/downgrade based on price
            if status == "active":
                # Subscription is active, check the plan
                plan = subscription.get("plan")
                if plan:
                    # Plan details
                    plan_id = plan.get("id")
                    plan_nickname = plan.get("nickname")
                    plan_amount = plan.get("amount") / 100  # Convert to dollars
                    plan_interval = plan.get("interval")
                    
                    # Log the subscription update
                    logger.info(f"Subscription updated: {plan_nickname} (${plan_amount:.2f} {plan_interval})")
                    
                    # Update subscription in database
                    subscription_service.update_subscription_from_webhook(
                        user_id_val, 
                        plan_nickname, 
                        subscription
                    )
                    logger.info(f"Updated subscription for user {user_id_val} to plan {plan_nickname}")
                else:
                    logger.warning(f"No plan information found in subscription update for user {user_id_val}")
            else:
                # Inactive status, handle accordingly
                logger.info(f"Subscription inactive for user {user_id_val}, status: {status}")
                update_subscription_status(user_id_val, "inactive")
        else:
            logger.warning(f"No account found for customer ID {customer_id} in subscription update")

    elif event_type == "customer.subscription.deleted":
        # Subscription deleted
        logger.info("Subscription deleted event received")
        subscription = data_object
        customer_id = subscription.get("customer")

        # 1. Find the associated user account
        account = collection.database.Accounts.find_one({
            "$or": [{"stripeCustomerId": customer_id}, {"userId": customer_id}, {"ownerId": customer_id}]
        })

        if account:
            user_id_val = account.get("userId") or account.get("ownerId") # Renamed user_id to user_id_val
            
            # Update user's subscription status to FREE/cancelled
            try:
                # Update account document
                collection.database.Accounts.update_one(
                    {"id": account["id"]}, # Use account's own id
                    {
                        "$set": {
                            "subscriptionStatus": "cancelled",
                            "stripeSubscriptionId": None,  # Clear the subscription ID
                        }
                    }
                )

                # Update subscription record
                collection.database.Subscriptions.update_one(
                    {"user_id": user_id_val, "status": "active"},
                    {
                        "$set": {
                            "status": "cancelled",
                            "end_date": datetime.utcnow(),
                        }
                    }
                )

                # Reset credits to FREE plan
                from backend.services.creditService import update_subscription_credits
                update_subscription_credits(user_id_val, "FREE")
                
                logger.info(f"Successfully cancelled subscription for user {user_id_val}")
            except Exception as e:
                logger.error(f"Failed to cancel subscription: {str(e)}")
        else:
            logger.warning(f"No account found for customer ID {customer_id} in subscription deletion")

    elif event_type == "invoice.payment_failed":
        # Payment failed
        logger.info("Invoice payment failed event received")
        invoice = data_object
        customer_id = invoice.get("customer")
        subscription_id = invoice.get("subscription")

        # 1. Find the associated user account
        account = collection.database.Accounts.find_one({
            "$or": [{"stripeCustomerId": customer_id}, {"userId": customer_id}, {"ownerId": customer_id}]
        })

        if account:
            user_id_val = account.get("userId") or account.get("ownerId") # Renamed user_id to user_id_val
            
            # Mark subscription as past_due in our database
            collection.database.Accounts.update_one(
                {"id": account["id"]}, # Use account's own id
                {
                    "$set": {
                        "subscriptionStatus": "past_due",
                    }
                }
            )

            # Also update in Subscriptions collection
            collection.database.Subscriptions.update_one(
                {"user_id": user_id_val, "status": "active"},
                {
                    "$set": {
                        "status": "past_due",
                    }
                }
            )

            logger.info(f"Subscription marked as past_due for user {user_id_val}")
        else:
            logger.warning(f"No account found for customer ID {customer_id} in invoice payment failed")

    else:
        logger.info(f"No specific handler for event type: {event_type}")
