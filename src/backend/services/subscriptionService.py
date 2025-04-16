from datetime import datetime, timedelta
from backend.database.mongo_connection import collection
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self):
        self.accounts_collection = collection.database.Accounts
        self.subscriptions_collection = collection.database.subscriptions_collection
    
    def get_user_subscription(self, user_id):
        """Get a user's current subscription details"""
        account = self.accounts_collection.find_one({"userId": user_id})
        if not account:
            logger.warning(f"No account found for user {user_id}")
            return None
        
        subscription_data = {
            "plan": account.get("subscriptionPlan", "Free"),
            "status": account.get("subscriptionStatus", "inactive"),
            "end_date": account.get("subscriptionEnd", None)
        }
        
        return subscription_data
    
    def update_user_subscription(self, user_id, plan_name, stripe_session):
        """
        Update a user's subscription based on the purchased plan.
        
        Args:
            user_id: The user's ID
            plan_name: The name of the plan (e.g. "Pro", "Enterprise")
            stripe_session: The Stripe checkout session object
        """
        try:
            # Get the amount paid in the Stripe session
            amount_paid = stripe_session['amount_total'] / 100  # Convert cents to dollars
            
            # Retrieve the user's account
            account = self.accounts_collection.find_one({"userId": user_id})
            if not account:
                raise ValueError(f"No account found for user {user_id}")
            
            # Calculate subscription end date (1 month from now)
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=30)
            
            # Update the user's subscription details
            update_result = self.accounts_collection.update_one(
                {"userId": user_id},
                {"$set": {
                    "subscriptionStatus": "active",
                    "subscriptionPlan": plan_name,
                    "subscriptionAmount": amount_paid,
                    "subscriptionStart": start_date.isoformat(),
                    "subscriptionEnd": end_date.isoformat(),
                    "lastUpdated": datetime.utcnow().isoformat()
                }}
            )
            
            if update_result.modified_count == 0:
                raise ValueError(f"Failed to update subscription for user {user_id}")
            
            # Also record in the subscriptions collection
            subscription_data = {
                "user_id": user_id,
                "plan": plan_name,
                "amount": amount_paid,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "status": "active",
                "payment_id": stripe_session.id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.subscriptions_collection.insert_one(subscription_data)
            
            return True
        except Exception as e:
            logger.error(f"Error updating subscription: {str(e)}")
            raise Exception(f"Error updating subscription: {str(e)}")