from datetime import datetime, timedelta
from backend.database.mongo_connection import collection
from backend.utils.subscription_access import PLAN_BENEFITS
import logging
import uuid
from dateutil.parser import parse as parse_date

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self):
        self.accounts_collection = collection.database.Accounts
        self.subscriptions_collection = collection.database.subscriptions_collection
        self.episodes_collection = collection.database.Episodes

    def _get_account(self, user_id):
        return self.accounts_collection.find_one({"userId": user_id}) or \
               self.accounts_collection.find_one({"ownerId": user_id})

    def get_user_subscription(self, user_id):
        """Get a user's current subscription details with benefits."""
        account = self._get_account(user_id)
        if not account:
            logger.warning(f"No account found for user {user_id} (tried both userId and ownerId)")
            return None

        status = account.get("subscriptionStatus", "inactive")
        plan = account.get("subscriptionPlan", "FREE").upper()

        subscription_data = {
            "plan": plan,
            "status": status,
            "start_date": account.get("subscriptionStart", None),
            "end_date": account.get("subscriptionEnd", None),
            "is_cancelled": status == "cancelled",
            "benefits": PLAN_BENEFITS.get(plan, PLAN_BENEFITS["FREE"])
        }

        return subscription_data

    def update_user_subscription(self, user_id, plan_name, stripe_session):
        """Update a user's subscription based on the purchased plan."""
        try:
            plan_name = plan_name.upper()
            if plan_name not in PLAN_BENEFITS:
                raise ValueError(f"Invalid plan name: {plan_name}. Must be one of {list(PLAN_BENEFITS.keys())}")

            amount_paid = stripe_session['amount_total'] / 100
            account = self._get_account(user_id)
            if not account:
                raise ValueError(f"No account found for user {user_id}")

            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=30) if plan_name != "FREE" else None
            filter_query = {"userId": user_id} if "userId" in account else {"ownerId": user_id}

            update_data = {
                "subscriptionStatus": "active",
                "subscriptionPlan": plan_name,
                "subscriptionAmount": amount_paid,
                "subscriptionStart": start_date.isoformat(),
                "lastUpdated": datetime.utcnow().isoformat()
            }
            if end_date:
                update_data["subscriptionEnd"] = end_date.isoformat()

            update_result = self.accounts_collection.update_one(filter_query, {"$set": update_data})
            if update_result.modified_count == 0:
                raise ValueError(f"Failed to update subscription for user {user_id}")

            subscription_data = {
                "_id": str(uuid.uuid4()),
                "user_id": user_id,
                "plan": plan_name,
                "amount": amount_paid,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat() if end_date else None,
                "status": "active",
                "payment_id": stripe_session.id,
                "created_at": datetime.utcnow().isoformat()
            }

            self.subscriptions_collection.insert_one(subscription_data)
            return True

        except Exception as e:
            logger.error(f"Error updating subscription for user {user_id} with plan {plan_name}: {str(e)}")
            raise Exception(f"Error updating subscription: {str(e)}")

    def can_create_episode(self, user_id):

        try:
            account = self._get_account(user_id)
            if not account:
                return False, "Account not found"

            sub = self.get_user_subscription(user_id)
            if not sub:
                return False, "Subscription info not found"

            benefits = sub["benefits"]
            plan = sub["plan"]

            episode_slots = benefits.get("episode_slots", 0)
            extra_slots = account.get("extra_episode_slots", 0)  # Optional extra slots
            total_allowed_slots = episode_slots + extra_slots

            if benefits.get("max_slots") == "Unlimited":
                return True, "Unlimited episodes allowed"

            now = datetime.utcnow()
            start = parse_date(sub["start_date"]) if sub.get("start_date") else now - timedelta(days=30)
            end = parse_date(sub["end_date"]) if sub.get("end_date") else now

            # Only count episodes that are NOT RSS-imported
            count = self.episodes_collection.count_documents({
                "userid": str(user_id),
                "created_at": {"$gte": start, "$lte": end},
                "$or": [
                    {"isImported": {"$exists": False}},
                    {"isImported": False}
                ]
            })

            if count < total_allowed_slots:
                return True, f"{count} < allowed {total_allowed_slots}"
            else:
                if extra_slots > 0:
                    return False, f"You’ve used your {episode_slots} base slots and all {extra_slots} extra slot(s). Upgrade your plan to create more episodes."
                else:
                    return False, f"You’ve used your {episode_slots} free episode slots. Upgrade your plan to unlock more."

        except Exception as e:
            logger.error(f"❌ Error checking create-episode permission for user {user_id}: {str(e)}")
            return False, "Internal server error"


