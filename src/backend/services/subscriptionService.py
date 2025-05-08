from datetime import datetime, timedelta, timezone
from backend.database.mongo_connection import collection
from backend.utils.subscription_access import PLAN_BENEFITS
import logging
import uuid
from dateutil.parser import parse as parse_date
from backend.services.activity_service import ActivityService  # Add this import
from dateutil.parser import parse as parse_date  
import stripe
from flask import current_app

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self):
        self.accounts_collection = collection.database.Accounts
        self.subscriptions_collection = collection.database.Subscriptions # Changed from subscriptions_collection
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
            "plan": account.get("subscriptionPlan", "FREE"),
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

            # Store current checkout session ID to avoid canceling our new subscription
            current_session_id = stripe_session.id
            logger.info(f"Current checkout session ID: {current_session_id}")

            # Check for and cancel any existing active subscriptions in Stripe
            try:
                
                
                # Initialize a list to track all subscriptions we find
                found_subscriptions = []
                
                # Look for ALL active subscriptions for this user, not just one
                existing_subscriptions = list(self.subscriptions_collection.find(
                    {"user_id": user_id, "status": "active"}
                ))
                
                logger.info(f"Found {len(existing_subscriptions)} active subscriptions in database for user {user_id}")
                
                # Process each subscription from our database
                for existing_sub in existing_subscriptions:
                    if existing_sub.get("payment_id") and existing_sub.get("payment_id") != current_session_id:
                        payment_id = existing_sub.get("payment_id")
                        
                        # If payment_id is a subscription ID (starts with "sub_")
                        if payment_id.startswith("sub_"):
                            logger.info(f"Found existing Stripe subscription ID: {payment_id} for user {user_id}")
                            found_subscriptions.append(payment_id)
                            
                        # If payment_id is a checkout session, try to get subscription from it
                        else:
                            try:
                                checkout_session = stripe.checkout.Session.retrieve(payment_id)
                                if checkout_session and hasattr(checkout_session, 'subscription'):
                                    stripe_subscription_id = checkout_session.subscription
                                    if stripe_subscription_id:
                                        logger.info(f"Retrieved subscription ID {stripe_subscription_id} from session {payment_id}")
                                        found_subscriptions.append(stripe_subscription_id)
                            except Exception as session_err:
                                logger.error(f"Error retrieving subscription from session {payment_id}: {session_err}")
                
                if account.get("email"):
                    try:
                        # Look up customer by email
                        customers = stripe.Customer.list(email=account.get("email"), limit=5)
                        if customers and customers.data:
                            for customer in customers.data:
                                logger.info(f"Found Stripe customer by email: {customer.id}")
                                
                                # Find active subscriptions for this customer
                                customer_subs = stripe.Subscription.list(
                                    customer=customer.id,
                                    status="active",
                                    limit=10
                                )
                                
                                if customer_subs and customer_subs.data:
                                    for sub in customer_subs.data:
                                        # Check if this subscription is just being created in this session
                                        if hasattr(stripe_session, 'subscription') and stripe_session.subscription == sub.id:
                                            logger.info(f"Skipping current subscription {sub.id} that's being created")
                                            continue
                                            
                                        logger.info(f"Found active subscription {sub.id} for customer {customer.id}")
                                        found_subscriptions.append(sub.id)
                    except Exception as customer_err:
                        logger.error(f"Error finding subscriptions by customer email: {customer_err}")
                
                if account.get("stripeCustomerId"):
                    try:
                        customer_id = account.get("stripeCustomerId")
                        customer_subs = stripe.Subscription.list(
                            customer=customer_id,
                            status="active",
                            limit=10
                        )
                        
                        if customer_subs and customer_subs.data:
                            for sub in customer_subs.data:
                                # Check if this subscription is just being created in this session
                                if hasattr(stripe_session, 'subscription') and stripe_session.subscription == sub.id:
                                    logger.info(f"Skipping current subscription {sub.id} that's being created")
                                    continue
                                    
                                logger.info(f"Found active subscription {sub.id} for customer ID {customer_id}")
                                found_subscriptions.append(sub.id)
                    except Exception as direct_customer_err:
                        logger.error(f"Error finding subscriptions by direct customer ID: {direct_customer_err}")
                
                # Now cancel all found subscriptions
                # Remove duplicates
                found_subscriptions = list(set(found_subscriptions))
                logger.info(f"Attempting to cancel {len(found_subscriptions)} subscriptions: {found_subscriptions}")
                
                for subscription_id in found_subscriptions:
                    try:
                        # First verify the subscription exists and is active
                        sub_check = stripe.Subscription.retrieve(subscription_id)
                        logger.info(f"Subscription {subscription_id} status: {sub_check.status}, cancel_at_period_end: {sub_check.cancel_at_period_end}")
                        
                        if sub_check.status == "active" and not sub_check.cancel_at_period_end:
                            # Cancel at period end keeps access until end of current period
                            cancelled_subscription = stripe.Subscription.modify(
                                subscription_id,
                                cancel_at_period_end=True
                            )
                            logger.info(f"Successfully canceled subscription {subscription_id} at period end")
                            
                            # Update our database record - find all records with this payment_id
                            self.subscriptions_collection.update_many(
                                {"$or": [
                                    {"payment_id": subscription_id},
                                    {"stripe_subscription_id": subscription_id}
                                ]},
                                {"$set": {"status": "cancelled", "cancelled_at": datetime.utcnow().isoformat()}}
                            )
                    except Exception as cancel_err:
                        logger.error(f"Error canceling subscription {subscription_id}: {cancel_err}")
            
            except Exception as cancel_process_err:
                logger.error(f"Error during subscription cancellation process: {cancel_process_err}")
                # Continue with creating the new subscription even if cancellation fails

            # Rest of your existing code for creating the new subscription
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=30)

            # Get the plan benefits from subscription_access.py
            plan_benefits = PLAN_BENEFITS.get(plan_name.upper(), PLAN_BENEFITS["FREE"])

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
                        "benefits": plan_benefits,  # Add the plan benefits
                    }
                },
            )

            if update_result.modified_count == 0:
                raise ValueError(f"Failed to update subscription for user {user_id}")

            # Mark all other active subscriptions for this user as inactive BEFORE inserting the new one
            try:
                update_inactive_result = self.subscriptions_collection.update_many(
                    {"user_id": user_id, "status": "active"},
                    {"$set": {"status": "inactive", "updated_at": datetime.utcnow().isoformat()}}
                )
                logger.info(f"Marked {update_inactive_result.modified_count} previous active subscriptions as inactive for user {user_id}")
            except Exception as inactive_err:
                logger.error(f"Error marking previous subscriptions as inactive for user {inactive_err}", exc_info=True)
                # Continue even if this fails, priority is the new subscription

            # Also record in the subscriptions collection
            subscription_data = {
                "_id": str(uuid.uuid4()),
                "user_id": user_id,
                "plan": account.get("subscriptionPlan", "FREE"),
                "amount": amount_paid,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat() if end_date else None,
                "status": "active",
                "payment_id": stripe_session.id,
                "created_at": datetime.utcnow().isoformat(),
                "benefits": plan_benefits,  # Add the plan benefits
            }

            self.subscriptions_collection.insert_one(subscription_data)

            # Update the user's credits based on the subscription plan
            try:
                from backend.services.creditService import update_subscription_credits
                
                # This will update the subCredits to match the plan's credit allocation
                updated_credits = update_subscription_credits(user_id, plan_name)
                logger.info(f"Updated credits for user {user_id} to {plan_benefits.get('credits', 0)} credits based on {plan_name} plan")
                
                # Include the updated credit information in the return value
                return True, updated_credits
            except Exception as credit_err:
                logger.error(f"Failed to update subscription credits: {credit_err}", exc_info=True)
                return True, None

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
                        "credits": plan_benefits.get("credits", 0),  # Add credits to the activity log
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

    def update_subscription_from_webhook(self, user_id, plan_name, stripe_subscription):
        """
        Update a user's subscription from a webhook event.
        This is similar to update_user_subscription but optimized for webhook events.
        """
        try:
            start_date = datetime.fromtimestamp(stripe_subscription.current_period_start, tz=timezone.utc)
            end_date = datetime.fromtimestamp(stripe_subscription.current_period_end, tz=timezone.utc)
            
            # Get the amount from the subscription items
            amount_paid = 0
            for item in stripe_subscription.items.data:
                amount_paid += item.price.unit_amount / 100  # Convert cents to dollars
            
            # Get the plan benefits
            plan_benefits = PLAN_BENEFITS.get(plan_name.upper(), PLAN_BENEFITS["FREE"])
            
            # Find account to update
            filter_query = {"userId": user_id}
            account = self.accounts_collection.find_one(filter_query)
            if not account:
                filter_query = {"ownerId": user_id}
                account = self.accounts_collection.find_one(filter_query)
            
            if not account:
                raise ValueError(f"No account found for user {user_id}")
            
            # Update account record
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
                        "benefits": plan_benefits,
                        "stripeCustomerId": stripe_subscription.customer,
                    }
                },
            )
            
            if update_result.modified_count == 0:
                logger.warning(f"No changes made to account for user {user_id}")
            
            # Update any existing active subscription to inactive
            self.subscriptions_collection.update_many(
                {"user_id": user_id, "status": "active"},
                {"$set": {"status": "inactive", "updated_at": datetime.utcnow().isoformat()}}
            )
            
            # Create a new subscription record
            subscription_data = {
                "_id": str(uuid.uuid4()),
                "user_id": user_id,
                "plan": plan_name,
                "amount": amount_paid,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "status": "active",
                "payment_id": stripe_subscription.id,
                "stripe_subscription_id": stripe_subscription.id, 
                "created_at": datetime.utcnow().isoformat(),
                "benefits": plan_benefits,
            }
            
            self.subscriptions_collection.insert_one(subscription_data)
            
            # Update user's credits based on the subscription plan
            from backend.services.creditService import update_subscription_credits
            updated_credits = update_subscription_credits(user_id, plan_name)
            
            # Log the subscription update activity
            self.activity_service.log_activity(
                user_id=user_id,
                activity_type="subscription_updated",
                description=f"Subscription updated to '{plan_name}' plan via webhook.",
                details={
                    "plan": plan_name,
                    "amount": amount_paid,
                    "end_date": end_date.isoformat(),
                    "credits": plan_benefits.get("credits", 0),
                },
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating subscription from webhook for user {user_id}: {str(e)}")
            raise Exception(f"Error updating subscription: {str(e)}")

    def handle_subscription_renewal(self, user_id, stripe_subscription):
        """
        Handle subscription renewal from Stripe webhook events.
        Updates subscription dates and resets monthly credits.
        
        Args:
            user_id: The user's ID
            stripe_subscription: The Stripe subscription object
            
        Returns:
            bool: Success status
        """
        try:
            # Get current account with subscription data
            account = self._get_account(user_id)
            if not account:
                raise ValueError(f"No account found for user {user_id}")
            
            # IMPORTANT: Store the current plan first to use as fallback
            current_plan = account.get("subscriptionPlan", "FREE")
            logger.info(f"Current plan before renewal: {current_plan}")
                
            # Calculate proper renewal dates
            # If the account has an existing subscription end date, use that as the base
            if account.get("subscriptionEnd"):
                try:
                    # Parse the current end date
                    current_end_date = datetime.fromisoformat(account["subscriptionEnd"].replace("Z", "+00:00"))
                    
                    # Calculate new dates - add one month to the current end date
                    new_start_date = current_end_date
                    new_end_date = current_end_date + timedelta(days=30)  # Add 30 days for the next cycle
                    
                    logger.info(f"Renewing subscription from {current_end_date.isoformat()} to {new_end_date.isoformat()}")
                except (ValueError, AttributeError) as e:
                    logger.error(f"Error parsing current subscription end date: {str(e)}")
                    # Fall back to Stripe dates if there's an error
                    new_start_date = datetime.fromtimestamp(stripe_subscription.current_period_start, tz=timezone.utc)
                    new_end_date = datetime.fromtimestamp(stripe_subscription.current_period_end, tz=timezone.utc)
            else:
                # No existing end date, use Stripe dates
                new_start_date = datetime.fromtimestamp(stripe_subscription.current_period_start, tz=timezone.utc)
                new_end_date = datetime.fromtimestamp(stripe_subscription.current_period_end, tz=timezone.utc)
            
            # Default plan to current plan - critical change to preserve plan if extraction fails
            plan_name = current_plan.upper() if isinstance(current_plan, str) else "FREE"
            amount_paid = 0
            
            # Try to extract plan information from Stripe only if needed
            try:
                if hasattr(stripe_subscription, 'items') and hasattr(stripe_subscription.items, 'data'):
                    for item in stripe_subscription.items.data:
                        if hasattr(item, 'price') and hasattr(item.price, 'unit_amount'):
                            amount_paid += item.price.unit_amount / 100  # Convert cents to dollars
                            
                            # Get product information to determine the plan
                            try:
                                if hasattr(item.price, 'product'):
                                    product_id = item.price.product
                                    product = stripe.Product.retrieve(product_id)
                                    extracted_plan = product.metadata.get("plan") or product.name
                                    if extracted_plan:
                                        logger.info(f"Extracted plan from Stripe product: {extracted_plan}")
                                        # Only override current plan if we successfully extracted one
                                        if extracted_plan.upper() in PLAN_BENEFITS:
                                            plan_name = extracted_plan.upper()
                                        elif "PRO" in extracted_plan.upper():
                                            plan_name = "PRO"
                                        elif "STUDIO" in extracted_plan.upper():
                                            plan_name = "STUDIO"
                                        elif "ENTERPRISE" in extracted_plan.upper():
                                            plan_name = "ENTERPRISE"
                            except Exception as e:
                                logger.error(f"Error retrieving plan name from product: {str(e)}")
                                # Continue with current plan if extraction fails
                else:
                    # Try alternative method to get subscription data
                    logger.info("Items data not available on subscription object, trying direct lookup")
                    # If stripe_subscription.id is available, we can retrieve the full subscription
                    if hasattr(stripe_subscription, 'id'):
                        try:
                            full_subscription = stripe.Subscription.retrieve(
                                stripe_subscription.id,
                                expand=['items.data.price.product']
                            )
                            
                            # Process the full subscription data
                            if hasattr(full_subscription, 'items') and hasattr(full_subscription.items, 'data'):
                                for item in full_subscription.items.data:
                                    if hasattr(item, 'price'):
                                        amount_paid += item.price.unit_amount / 100
                                        if hasattr(item.price, 'product') and item.price.product:
                                            extracted_plan = item.price.product.metadata.get("plan") or item.price.product.name
                                            if extracted_plan:
                                                logger.info(f"Extracted plan from full subscription: {extracted_plan}")
                                                # Only override current plan if we successfully extracted one
                                                if extracted_plan.upper() in PLAN_BENEFITS:
                                                    plan_name = extracted_plan.upper()
                                                elif "PRO" in extracted_plan.upper():
                                                    plan_name = "PRO"
                                                elif "STUDIO" in extracted_plan.upper():
                                                    plan_name = "STUDIO"
                                                elif "ENTERPRISE" in extracted_plan.upper():
                                                    plan_name = "ENTERPRISE"
                        except Exception as e:
                            logger.error(f"Error retrieving full subscription: {str(e)}")
                            # Continue with current plan if extraction fails
            except Exception as e:
                logger.error(f"Error processing subscription items: {str(e)}")
                # Continue with current plan if extraction fails
            
            # If after all attempts we still don't have a valid plan in PLAN_BENEFITS, use current plan
            if plan_name not in PLAN_BENEFITS:
                logger.warning(f"Plan name '{plan_name}' not found in PLAN_BENEFITS, using current plan '{current_plan}'")
                plan_name = current_plan.upper() if isinstance(current_plan, str) else "FREE"
            
            logger.info(f"Final plan name for renewal: {plan_name}")
                
            # Get the plan benefits
            plan_benefits = PLAN_BENEFITS.get(plan_name, PLAN_BENEFITS["FREE"])
            
            # For pricing, use standard prices based on plan if not determined from Stripe
            if amount_paid == 0:
                plan_prices = {"PRO": 29.99, "STUDIO": 69.00, "ENTERPRISE": 199.00, "FREE": 0}
                amount_paid = plan_prices.get(plan_name, 0)
            
            # Determine which field we should use to query the account
            filter_query = {"userId": user_id} if "userId" in account else {"ownerId": user_id}
            
            # Update account record with new dates
            update_result = self.accounts_collection.update_one(
                filter_query,
                {
                    "$set": {
                        "subscriptionStatus": "active",
                        "subscriptionPlan": plan_name,  # Make sure it's the correct case
                        "subscriptionAmount": amount_paid,
                        "subscriptionStart": new_start_date.isoformat(),
                        "subscriptionEnd": new_end_date.isoformat(),
                        "lastUpdated": datetime.utcnow().isoformat(),
                        "benefits": plan_benefits,
                        "stripeCustomerId": stripe_subscription.customer if hasattr(stripe_subscription, 'customer') else None,
                    }
                },
            )
            
            if update_result.modified_count == 0:
                logger.warning(f"No changes made to account for user {user_id} during renewal")
            
            # Update any existing active subscription to inactive
            self.subscriptions_collection.update_many(
                {"user_id": user_id, "status": "active"},
                {"$set": {"status": "inactive", "updated_at": datetime.utcnow().isoformat()}}
            )
            
            # Create a new subscription record
            subscription_data = {
                "_id": str(uuid.uuid4()),
                "user_id": user_id,
                "plan": plan_name,  # Make sure it's the correct case
                "amount": amount_paid,
                "start_date": new_start_date.isoformat(),
                "end_date": new_end_date.isoformat(),
                "status": "active",
                "payment_id": stripe_subscription.id if hasattr(stripe_subscription, 'id') else None,
                "stripe_subscription_id": stripe_subscription.id if hasattr(stripe_subscription, 'id') else None, 
                "created_at": datetime.utcnow().isoformat(),
                "benefits": plan_benefits,
                "is_renewal": True  # Mark this as a renewal
            }
            
            self.subscriptions_collection.insert_one(subscription_data)
            
            # Update user's credits based on the subscription plan
            from backend.services.creditService import update_subscription_credits
            updated_credits = update_subscription_credits(user_id, plan_name)
            
            # Log the renewal activity
            self.activity_service.log_activity(
                user_id=user_id,
                activity_type="subscription_renewed",
                description=f"Subscription renewed for '{plan_name}' plan.",
                details={
                    "plan": plan_name,
                    "amount": amount_paid,
                    "start_date": new_start_date.isoformat(),
                    "end_date": new_end_date.isoformat(),
                    "credits": plan_benefits.get("credits", 0),
                },
            )
            
            logger.info(f"Successfully processed subscription renewal for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling subscription renewal for user {user_id}: {str(e)}", exc_info=True)
            raise Exception(f"Error handling subscription renewal: {str(e)}")

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
            extra_slots = account.get("unlockedExtraEpisodeSlots", 0)
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





