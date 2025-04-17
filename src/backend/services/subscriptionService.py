from datetime import datetime, timedelta
from backend.database.mongo_connection import collection
import logging
import uuid

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self):
        self.accounts_collection = collection.database.Accounts
        self.subscriptions_collection = collection.database.subscriptions_collection
    
    def get_user_subscription(self, user_id):
        """Get a user's current subscription details"""
        # First try looking up by userId
        account = self.accounts_collection.find_one({"userId": user_id})
        
        # If not found, try looking up by ownerId (for backward compatibility)
        if not account:
            account = self.accounts_collection.find_one({"ownerId": user_id})
            
        if not account:
            logger.warning(f"No account found for user {user_id} (tried both userId and ownerId)")
            return None
        
        status = account.get("subscriptionStatus", "inactive")
        
        subscription_data = {
            "plan": account.get("subscriptionPlan", "Free"),
            "status": status,
            "end_date": account.get("subscriptionEnd", None),
            "is_cancelled": status == "cancelled"
        }
        
        return subscription_data
    
    def update_user_subscription(self, user_id, plan_name, stripe_session):
        """
        Update a user's subscription based on the purchased plan.
        """
        try:
            # Get the amount paid in the Stripe session
            amount_paid = stripe_session['amount_total'] / 100  # Convert cents to dollars
            
            # First try to find account by userId
            account = self.accounts_collection.find_one({"userId": user_id})
            
            # If not found, try looking up by ownerId
            if not account:
                account = self.accounts_collection.find_one({"ownerId": user_id})
                
            if not account:
                raise ValueError(f"No account found for user {user_id} (tried both userId and ownerId)")
            
            # Calculate subscription end date (1 month from now)
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=30)
            
            # Update the user's subscription details - use the field that was found
            filter_query = {"userId": user_id} if "userId" in account else {"ownerId": user_id}
            
            update_result = self.accounts_collection.update_one(
                filter_query,
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
                "_id": str(uuid.uuid4()),  # Generate a UUID string for _id
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