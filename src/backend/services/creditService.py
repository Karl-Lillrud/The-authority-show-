# src/backend/services/creditService.py
from datetime import datetime
import uuid
from backend.database.mongo_connection import collection
from backend.utils.credit_costs import CREDIT_COSTS
from backend.utils.subscription_access import PLAN_BENEFITS
from backend.services.creditManagement import CreditService
from datetime import datetime, timezone
import logging
from backend.repository.credits_repository import (
    get_credits_by_user_id,
    update_credits,
    log_credit_transaction,
)
from backend.services.activity_service import (
    ActivityService,
)

logger = logging.getLogger(__name__)


def get_store_credits(user_id):
    credits = get_credits_by_user_id(user_id)
    if credits:
        credits["_id"] = str(credits["_id"])
    return credits


def consume_credits(user_id, feature_name):
    cost = CREDIT_COSTS.get(feature_name)
    if cost is None:
        raise ValueError("Invalid feature name.")

    credits = get_credits_by_user_id(user_id)
    if not credits:
        raise ValueError("No credits account found for user.")

    available = credits.get("availableCredits", 0)
    if available < cost:
        logger.warning(
            f"User {user_id} has {available} credits, but {cost} required for {feature_name}"
        )
        raise ValueError("Insufficient credits.")

    new_available = available - cost
    new_used = credits.get("usedCredits", 0) + cost

    update_credits(
        user_id,
        {
            "availableCredits": new_available,
            "usedCredits": new_used,
            "lastUpdated": datetime.utcnow(),
        },
    )

    log_credit_transaction(
        user_id, {"feature": feature_name, "cost": cost, "timestamp": datetime.utcnow()}
    )

    # Log credit consumption activity
    try:
        activity_service = ActivityService()
        activity_service.log_activity(
            user_id=user_id,
            activity_type="credits_consumed",
            description=f"Credits consumed for feature: {feature_name}",
            details={
                "feature": feature_name,
                "cost": cost,
                "remaining_credits": new_available,
            },
        )
    except Exception as log_e:
        logger.error(f"Failed to log credits_consumed activity: {log_e}")

    return {"remaining": new_available, "used": new_used}


def initialize_credits(user_id: str, initial_amount=3000):
    """Initialize credits for a new user."""
    existing = get_credits_by_user_id(user_id)
    if not existing:

        credit_doc = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "availableCredits": initial_amount,
            "usedCredits": 0,
            "creditLimit": 3000,
            "lastUpdated": datetime.utcnow(),
            "creditsHistory": [
                {
                    "_id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow(),
                    "amount": initial_amount,
                    "type": "initial",
                    "description": "Initial credit allocation",
                    "status": "completed",
                }
            ],
        }
        # Use insert_one without allowing _id conversion
        collection.database.Credits.insert_one(credit_doc)

        # Log credit initialization activity
        try:
            activity_service = ActivityService()
            activity_service.log_activity(
                user_id=user_id,
                activity_type="credits_initialized",
                description="User credits account initialized",
                details={"initial_amount": initial_amount},
            )
        except Exception as log_e:
            logger.error(f"Failed to log credits_initialized activity: {log_e}")


def deduct_credits(user_id, feature_name):
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

    update_credits(
        user_id,
        {
            "availableCredits": new_available,
            "usedCredits": new_used,
            "lastUpdated": datetime.utcnow(),
        },
    )

    log_credit_transaction(
        user_id, {"feature": feature_name, "cost": cost, "timestamp": datetime.utcnow()}
    )

    # Log credit deduction activity
    try:
        activity_service = ActivityService()
        activity_service.log_activity(
            user_id=user_id,
            activity_type="credits_deducted",
            description=f"Credits deducted for feature: {feature_name}",
            details={
                "feature": feature_name,
                "cost": cost,
                "remaining_credits": new_available,
            },
        )
    except Exception as log_e:
        logger.error(f"Failed to log credits_deducted activity: {log_e}")

    return {"remaining": new_available}


def update_subscription_credits(user_id, plan_name):
    """
    Updates a user's subCredits based on their subscription plan.
    This REPLACES their existing subCredits with the new plan's allocation.

    Args:
        user_id: The user's ID
        plan_name: The name of the plan (FREE, PRO, STUDIO, ENTERPRISE)

    Returns:
        dict: Updated credit information
    """

    logger = logging.getLogger(__name__)

    # Get the plan benefits
    plan_name = plan_name.upper()  # Ensure consistent casing
    if plan_name not in PLAN_BENEFITS:
        raise ValueError(f"Invalid plan name: {plan_name}")

    # Get credit allocation for the plan
    sub_credits = PLAN_BENEFITS[plan_name].get("credits", 0)

    # Use the CreditService to manage subCredits
    credit_service = CreditService()

    # Get user credits, initialize if needed
    store_credits = credit_service.get_store_credits(user_id)
    if not store_credits:
        # Initialize with the subscription plan credits as subCredits
        credit_service.initialize_credits(
            user_id, initial_sub=sub_credits, initial_user=0
        )
        logger.info(
            f"Initialized credits for new user {user_id} with {sub_credits} subCredits from {plan_name} plan"
        )
        return credit_service.get_store_credits(user_id)

    # Get the current credits document
    credits_doc = credit_service._get_raw_credits(user_id)
    old_sub = credits_doc.get("subCredits", 0)
    store_credits = credits_doc.get("storeCredits", 0)

    # IMPORTANT: Update directly in the database to SET (not increment) subCredits
    # This is the key fix - use $set instead of $inc to replace the credits
    credit_service.credits_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "subCredits": sub_credits,
                "lastUpdated": datetime.now(timezone.utc),
            }
        },
    )

    # Log the transaction with proper description
    credit_service._log_transaction(
        user_id,
        {
            "type": "adjustment",  # Changed from "subscription_change" to "adjustment"
            "amount": sub_credits - old_sub,  # Net change (can be negative or positive)
            "description": f"Reset subCredits from {old_sub} to {sub_credits} for {plan_name} plan",
            "balance_after": {"subCredits": sub_credits, "storeCredits": store_credits},
        },
    )

    # Log credit update activity
    try:
        activity_service = ActivityService()  # Already imported
        activity_service.log_activity(
            user_id=user_id,
            activity_type="credits_updated_by_subscription",
            description=f"Credits updated to {sub_credits} for plan {plan_name}",
            details={
                "plan": plan_name,
                "new_sub_credits": sub_credits,
                "old_sub_credits": old_sub,
                "change_amount": sub_credits - old_sub,
            },
        )
    except Exception as log_e:
        logger.error(f"Failed to log credits_updated_by_subscription activity: {log_e}")

    logger.info(
        f"Updated subscription subCredits for user {user_id}: replaced {old_sub} with {sub_credits} from {plan_name} plan"
    )
    return credit_service.get_store_credits(user_id)


def reset_monthly_credits(user_id, plan_name):
    """
    Reset a user's monthly credits based on their subscription plan.
    Called when a subscription renews.
    """
    try:

        # Get the credits amount for this plan
        plan_benefits = PLAN_BENEFITS.get(plan_name.upper(), PLAN_BENEFITS["FREE"])
        credits_amount = plan_benefits.get("credits", 0)

        if credits_amount <= 0:
            logger.info(f"No monthly credits to reset for plan {plan_name}")
            return False

        # Find the user's account
        account = collection.database.Accounts.find_one(
            {"$or": [{"userId": user_id}, {"ownerId": user_id}]}
        )

        if not account:
            logger.error(f"Account not found for user {user_id}")
            return False

        # Update the subCredits field to reset monthly credits
        result = collection.database.Accounts.update_one(
            {"_id": account["_id"]}, {"$set": {"subCredits": credits_amount}}
        )

        if result.modified_count > 0:
            logger.info(f"Reset monthly credits to {credits_amount} for user {user_id}")

            # Log the credit reset
            activity_service = ActivityService()
            activity_service.log_activity(
                user_id=user_id,
                activity_type="credits_reset",
                description=f"Monthly subscription credits reset to {credits_amount}",
                details={"plan": plan_name, "credits": credits_amount},
            )

            return True
        else:
            logger.warning(f"No changes made to credits for user {user_id}")
            return False

    except Exception as e:
        logger.error(f"Error resetting monthly credits: {str(e)}")
        return False
