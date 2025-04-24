from datetime import datetime, timedelta
from backend.database.mongo_connection import collection
from backend.utils.subscription_access import PLAN_BENEFITS
import logging
import uuid
from dateutil.parser import parse as parse_date
from backend.services.activity_service import ActivityService  # Add this import

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self):
        self.accounts_collection = collection.database.Accounts
        self.subscriptions_collection = collection.database.subscriptions_collection
        self.activity_service = ActivityService()  # Add this line
        self.episodes_collection = collection.database.Episodes

    def _get_account(self, user_id):
        """Helper to retrieve account by either userId or ownerId."""
        account = self.accounts_collection.find_one({"userId": user_id})
        if not account:
            account = self.accounts_collection.find_one({"ownerId": user_id})
        return account
        

    def get_user_subscription(self, user_id):
        """Get a user's current subscription details"""
        account = self._get_account(user_id)
        if not account:
            logger.warning(f"No account found for user {user_id}")
            return None

        status = account.get("subscriptionStatus", "inactive")
        plan = account.get("subscriptionPlan", "free")

        subscription_data = {
            "plan": plan,
            "status": status,
            "start_date": account.get("subscriptionStart"),
            "end_date": account.get("subscriptionEnd"),
            "is_cancelled": status == "cancelled",
        }

        return subscription_data


    def update_user_subscription(self, user_id, plan_name, stripe_session):
        """
        Update a user's subscription based on the purchased plan.
        """
        try:
            # Get the amount paid in the Stripe session
            amount_paid = (
                stripe_session["amount_total"] / 100
            )  # Convert cents to dollars

            # First try to find account by userId
            account = self.accounts_collection.find_one({"userId": user_id})

            # If not found, try looking up by ownerId
            if not account:
                account = self.accounts_collection.find_one({"ownerId": user_id})

            if not account:
                raise ValueError(
                    f"No account found for user {user_id} (tried both userId and ownerId)"
                )

            # Calculate subscription end date (1 month from now)
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=30)

            # Update the user's subscription details - use the field that was found
            filter_query = (
                {"userId": user_id} if "userId" in account else {"ownerId": user_id}
            )

            update_result = self.accounts_collection.update_one(
                filter_query,
                {
                    "$set": {
                        "subscriptionStatus": "active",
                        "subscriptionPlan": plan_name,
                        "subscriptionAmount": amount_paid,
                        "subscriptionStart": start_date.isoformat(),
                        "subscriptionEnd": end_date.isoformat(),
                        "lastUpdated": datetime.utcnow().isoformat(),
                    }
                },
            )

            if update_result.modified_count == 0:
                raise ValueError(f"Failed to update subscription for user {user_id}")

            # Also record in the subscriptions collection
            subscription_data = {
                "_id": str(uuid.uuid4()),
                "user_id": user_id,
                "plan": plan_name,
                "amount": amount_paid,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat() if end_date else None,
                "status": "active",
                "payment_id": stripe_session.id,
                "created_at": datetime.utcnow().isoformat(),
            }

            self.subscriptions_collection.insert_one(subscription_data)

            # --- Log subscription activity ---
            try:
                self.activity_service.log_activity(
                    user_id=user_id,
                    activity_type="subscription_updated",
                    description=f"Subscription updated to '{plan_name}' plan.",
                    details={
                        "plan": plan_name,
                        "amount": amount_paid,
                        "end_date": end_date.isoformat(),
                    },
                )
            except Exception as act_err:
                logger.error(
                    f"Failed to log subscription_updated activity: {act_err}",
                    exc_info=True,
                )
            # --- End activity log ---

            return True

        except Exception as e:
            logger.error(
                f"Error updating subscription for user {user_id} with plan {plan_name}: {str(e)}"
            )
            raise Exception(f"Error updating subscription: {str(e)}")

    def can_create_episode(self, user_id, is_imported=False):
        try:
            account = self._get_account(user_id)
            if not account:
                return False, "Account not found"

            # ✅ Skip limit check entirely for imported episodes
            if is_imported:
                logger.info(f"🔁 Skipping episode slot check for imported episode by user {user_id}")
                return True, "Imported episodes are allowed regardless of limits"

            sub = self.get_user_subscription(user_id)
            if not sub:
                return False, "Subscription info not found"

            plan = sub["plan"].upper()
            benefits = PLAN_BENEFITS.get(plan, PLAN_BENEFITS["FREE"])

            episode_slots = benefits.get("episode_slots", 0)
            extra_slots = account.get("extra_episode_slots", 0)
            total_allowed_slots = episode_slots + extra_slots

            if benefits.get("max_slots") == "Unlimited":
                return True, "Unlimited episodes allowed"

            now = datetime.utcnow()
            start = parse_date(sub["start_date"]) if sub.get("start_date") else now - timedelta(days=30)
            end = parse_date(sub["end_date"]) if sub.get("end_date") else now

            count = self.episodes_collection.count_documents({
                "userid": str(user_id),
                "created_at": {"$gte": start, "$lte": end},
                "$or": [
                    {"isImported": {"$exists": False}},
                    {"isImported": False}
                ]
            })

            logger.info(f"📊 Found {count} regular (non-imported) episodes for user {user_id}")
            if count < total_allowed_slots:
                logger.info(f"✅ User {user_id} is within allowed limit: {count}/{total_allowed_slots}")
                return True, f"{count} < allowed {total_allowed_slots}"
            else:
                if extra_slots > 0:
                    return False, f"You’ve used your {episode_slots} base slots and all {extra_slots} extra slot(s)."
                else:
                    return False, f"You’ve used your {episode_slots} free episode slots. Upgrade to unlock more."

        except Exception as e:
            logger.error(f"❌ Error checking create-episode permission for user {user_id}: {str(e)}")
            return False, "Internal server error"





