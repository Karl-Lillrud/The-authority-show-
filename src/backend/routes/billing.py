# File: backend/routes/billing.py
from flask import Blueprint, request, jsonify, redirect, session, g
import stripe
import os
from backend.services.billingService import handle_successful_payment
from backend.services.subscriptionService import SubscriptionService
from backend.database.mongo_connection import collection
import logging
from datetime import datetime
from backend.services.creditManagement import CreditService

billing_bp = Blueprint("billing_bp", __name__)
subscription_service = SubscriptionService()
credit_service = CreditService()
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@billing_bp.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    user_id = g.user_id
    data = request.get_json()
    amount = data.get("amount")  # total amount (for validation)
    plan = data.get("plan")  # optional: "pro", "studio", etc.
    credits = data.get("credits")  # optional: how many credits to add

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    if not amount:
        return jsonify({"error": "Missing amount"}), 400

    try:
        # Build line_items array
        line_items = []
        metadata = {
            "user_id": user_id,
            "is_subscription": "true" if plan else "false",
            "plan": plan or "",
        }
        if credits:
            metadata["credits"] = str(credits)

        # Add credits line item if present
        if credits:
            line_items.append(
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": f"Credit Pack ({credits} credits)"},
                        "unit_amount": (
                            int(
                                (float(amount) - float(29.99 if plan == "pro" else 0))
                                * 100
                            )
                            if plan
                            else int(float(amount) * 100)
                        ),
                    },
                    "quantity": 1,
                }
            )

        # Add subscription line item if present
        if plan:
            # Map plan to price
            plan_prices = {
                "pro": 29.99,
                "studio": 69.00,
                # Add other plans as needed
            }
            plan_price = plan_prices.get(plan, float(amount))
            line_items.append(
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": f"{plan.capitalize()} Subscription"},
                        "unit_amount": int(plan_price * 100),
                        "recurring": {"interval": "month", "interval_count": 1},
                    },
                    "quantity": 1,
                }
            )

        # If both, mode must be "subscription"
        mode = "subscription" if plan else "payment"

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode=mode,
            success_url=f"{os.getenv('API_BASE_URL')}/credits/success?session_id={{CHECKOUT_SESSION_ID}}&plan={plan or ''}",
            cancel_url=f"{os.getenv('API_BASE_URL')}/credits/cancel",
            metadata=metadata,
        )

        return jsonify({"sessionId": checkout_session.id})
    except Exception as e:
        logger.error(f"Stripe session creation error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@billing_bp.route("/credits/success", methods=["GET"])
def payment_success():
    session_id = request.args.get("session_id")
    plan = request.args.get("plan", "")

    # Get user_id from Flask session
    user_id = g.user_id

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    if not session_id:
        return jsonify({"error": "Missing session ID"}), 400

    try:
        # Retrieve the Stripe session with expanded line_items
        stripe_session = stripe.checkout.Session.retrieve(
            session_id, expand=["line_items"]
        )

        # Check if this includes a subscription, credits, or both
        metadata = stripe_session.get("metadata", {})
        credits_to_add = int(metadata.get("credits", 0))
        has_subscription = metadata.get("is_subscription", "false") == "true"

        # Handle subscription if present
        if plan and has_subscription:
            result, updated_credits = subscription_service.update_user_subscription(
                user_id, plan, stripe_session
            )
            logger.info(f"Subscription updated for user {user_id}: {plan}")

        # Handle credits if present
        if credits_to_add > 0:
            handle_successful_payment(stripe_session, user_id)
            logger.info(f"Credits processed for user {user_id}: {credits_to_add}")

        # Redirect based on purchase type
        if plan and has_subscription:
            return redirect("/account?subscription_updated=true#settings-purchases")
        else:
            return redirect("/dashboard")
    except Exception as e:
        logger.error(f"Payment processing error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@billing_bp.route("/credits/cancel", methods=["GET"])
def payment_cancel():
    return redirect("/account")


@billing_bp.route("/api/subscription", methods=["GET"])
def get_subscription():
    user_id = g.user_id

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    try:
        subscription = subscription_service.get_user_subscription(user_id)
        if subscription:
            return jsonify({"subscription": subscription}), 200
        else:
            return jsonify({"error": "No subscription found"}), 404
    except Exception as e:
        logger.error(f"Error fetching subscription: {str(e)}")
        return jsonify({"error": str(e)}), 500


@billing_bp.route("/cancel-subscription", methods=["POST"])
def cancel_subscription():
    try:
        # Get Flask session object right away and store user_id
        # This prevents variable shadowing issues later
        flask_session = session  # Create a reference to Flask session
        user_id = flask_session.get("user_id")
        logger.info(f"Cancel subscription requested for user_id: {user_id}")

        # Debug: Print the full session
        logger.debug(f"Session contents: {flask_session}")

        # Also check g.user_id if session.user_id is not available
        if not user_id:
            user_id = getattr(g, "user_id", None)
            logger.info(f"Trying g.user_id instead: {user_id}")

        if not user_id:
            logger.error("Cancellation failed: User not authenticated")
            return jsonify({"error": "User not authenticated"}), 401
        # Find user's subscription
        account = collection.database.Accounts.find_one({"userId": user_id})
        logger.debug(f"Account found: {bool(account)}")
        if account:
            logger.debug(
                f"Account details: userId={account.get('userId')}, subscriptionStatus={account.get('subscriptionStatus')}, subscriptionPlan={account.get('subscriptionPlan')}"
            )

        if not account:
            # Try looking with ownerId as fallback
            logger.info(f"Account not found with userId, trying with ownerId...")
            account = collection.database.Accounts.find_one({"ownerId": user_id})
            if account:
                logger.info(f"Account found with ownerId")
                logger.debug(
                    f"Account details: ownerId={account.get('ownerId')}, subscriptionStatus={account.get('subscriptionStatus')}, subscriptionPlan={account.get('subscriptionPlan')}"
                )

        if not account:
            logger.error(f"Cancellation failed: Account not found for user {user_id}")
            return jsonify({"error": "Account not found"}), 404

        # Get the current subscription end date to include in the response
        subscription_end = account.get("subscriptionEnd")
        logger.info(f"Current subscription end date: {subscription_end}")

        # Check if subscription already cancelled
        if account.get("subscriptionStatus") == "cancelled":
            logger.info(f"Subscription already cancelled for user {user_id}")

            # Return info even if already cancelled
            end_date_display = None
            if subscription_end:
                try:
                    end_date = datetime.fromisoformat(
                        subscription_end.replace("Z", "+00:00")
                    )
                    end_date_display = end_date.strftime("%Y-%m-%d")
                except (ValueError, AttributeError) as e:
                    logger.error(f"Error parsing date: {e}")
                    end_date_display = subscription_end

            return (
                jsonify(
                    {
                        "message": "Subscription was already cancelled",
                        "endDate": end_date_display,
                        "willRenew": False,
                    }
                ),
                200,
            )

        # Find and cancel the Stripe subscription
        try:
            # First try to get the subscription ID from the account
            stripe_subscription_id = None
            
            # Check the payment record for subscription_id
            subscription_record = collection.database.Subscriptions.find_one( # Changed from subscriptions_collection
                {"user_id": user_id, "status": "active"}
            )
            
            # Check if payment_id is actually a subscription ID
            if subscription_record and subscription_record.get("payment_id"):
                payment_id = subscription_record.get("payment_id")
                # If it starts with 'sub_', it's likely a subscription ID
                if payment_id.startswith("sub_"):
                    stripe_subscription_id = payment_id
                    logger.info(f"Found subscription ID directly in payment_id: {stripe_subscription_id}")
                else:
                    logger.info(f"Payment ID is not a subscription ID: {payment_id}")
                    # Try to get session and retrieve subscription from there
                    try:
                        # Renamed from "session" to "checkout_session" to avoid conflict with Flask's session
                        checkout_session = stripe.checkout.Session.retrieve(payment_id)
                        if checkout_session and hasattr(checkout_session, 'subscription'):
                            stripe_subscription_id = checkout_session.subscription
                            logger.info(f"Retrieved subscription ID from session: {stripe_subscription_id}")
                    except Exception as session_error:
                        logger.error(f"Error retrieving session: {str(session_error)}")
            
            # If still no subscription ID, try the customer method
            if not stripe_subscription_id:
                # Try to find customer in Stripe
                customer_id = None
                if account.get("email"):
                    try:
                        customers = stripe.Customer.list(email=account.get("email"), limit=1)
                        if customers and customers.data:
                            customer_id = customers.data[0].id
                            logger.info(f"Found Stripe customer by email: {customer_id}")
                        
                        # If we found a customer ID, look for active subscriptions
                        if customer_id:
                            subscriptions = stripe.Subscription.list(
                                customer=customer_id,
                                status="active",
                                limit=5  # Get multiple in case there are several
                            )
                            if subscriptions and subscriptions.data:
                                for sub in subscriptions.data:
                                    logger.info(f"Found subscription: {sub.id} with status {sub.status}")
                                
                                # Use the first active subscription
                                stripe_subscription_id = subscriptions.data[0].id
                                logger.info(f"Selected subscription for cancellation: {stripe_subscription_id}")
                            else:
                                logger.warning(f"No active subscriptions found for customer {customer_id}")
                    except Exception as customer_error:
                        logger.error(f"Error with Stripe customer operations: {str(customer_error)}")
            
            # Now try to cancel the subscription if we found an ID
            if stripe_subscription_id:
                try:
                    # First verify the subscription exists and is active
                    sub_check = stripe.Subscription.retrieve(stripe_subscription_id)
                    logger.info(f"Subscription status: {sub_check.status}, cancel_at_period_end: {sub_check.cancel_at_period_end}")
                    
                    if sub_check.status == "active" and not sub_check.cancel_at_period_end:
                        # Cancel at period end keeps access until end of current period
                        cancelled_subscription = stripe.Subscription.modify(
                            stripe_subscription_id,
                            cancel_at_period_end=True
                        )
                        logger.info(f"Stripe subscription {stripe_subscription_id} cancelled successfully! New status: {cancelled_subscription.status}, cancel_at_period_end: {cancelled_subscription.cancel_at_period_end}")
                    else:
                        logger.info(f"Subscription already cancelled or not active: {sub_check.status}, cancel_at_period_end: {sub_check.cancel_at_period_end}")
                except stripe.error.StripeError as stripe_specific_error:
                    logger.error(f"Stripe API error cancelling subscription: {str(stripe_specific_error)}")
                    # Don't re-raise, continue with local cancellation
            else:
                logger.warning(f"No Stripe subscription ID found to cancel for user {user_id}")
                
        except Exception as stripe_error:
            logger.error(f"Error in Stripe cancellation process: {str(stripe_error)}")
            # Continue with local cancellation even if Stripe cancellation fails

        # Update subscription status to cancelled and change plan to FREE
        update_query = {"userId": user_id}
        if "ownerId" in account and not account.get("userId"):
            # Use ownerId for update if that's what we found
            update_query = {"ownerId": user_id}

        logger.debug(f"Update query: {update_query}")

        # Update both subscription status and plan to FREE
        update_result = collection.database.Accounts.update_one(
            update_query,
            {
                "$set": {
                    "subscriptionStatus": "cancelled",
                    "subscriptionPlan": "FREE",  # Set plan to FREE when cancelling
                    "lastUpdated": datetime.utcnow().isoformat(),
                }
            },
        )

        logger.info(
            f"Account update result: matched={update_result.matched_count}, modified={update_result.modified_count}"
        )

        if update_result.modified_count == 0:
            if update_result.matched_count > 0:
                logger.warning(
                    f"Document matched but not modified - likely already has same values"
                )
            else:
                logger.error(
                    f"Failed to update subscription status - no document matched"
                )
                return jsonify({"error": "Failed to update subscription status"}), 500

        # Also update in subscriptions collection if it exists
        subscription_result = collection.database.Subscriptions.update_one( # Changed from subscriptions_collection
            {"user_id": user_id, "status": "active"},
            {
                "$set": {
                    "status": "cancelled",
                    "plan": "FREE",  # Update plan in subscription collection too
                    "cancelled_at": datetime.utcnow().isoformat(),
                }
            },
        )

        logger.info(
            f"Subscription collection update result: matched={subscription_result.matched_count if subscription_result else 'N/A'}, modified={subscription_result.modified_count if subscription_result else 'N/A'}"
        )

        # Update user's credits to FREE plan credits
        try:
            from backend.utils.subscription_access import PLAN_BENEFITS
            from backend.services.creditService import update_subscription_credits

            # Reset credits to FREE tier after cancellation
            updated_credits = update_subscription_credits(user_id, "FREE")
            logger.info(
                f"Updated user credits to FREE plan after cancellation: {updated_credits}"
            )
        except Exception as credit_err:
            logger.error(
                f"Error updating credits after cancellation: {credit_err}",
                exc_info=True,
            )

        logger.info(
            f"Cancelled subscription for user {user_id} and downgraded to FREE plan. Account update: {update_result.modified_count}, Subscription update: {subscription_result.modified_count if subscription_result else 0}"
        )

        # Return the end date with the success message
        end_date_display = None
        if subscription_end:
            try:
                # If the date is stored as an ISO string, parse it for display
                end_date = datetime.fromisoformat(
                    subscription_end.replace("Z", "+00:00")
                )
                end_date_display = end_date.strftime("%Y-%m-%d")
                logger.debug(f"Formatted end date: {end_date_display}")
            except (ValueError, AttributeError) as e:
                # If there's an error parsing, just use the raw value
                logger.error(f"Error parsing end date: {e}")
                end_date_display = subscription_end

        return (
            jsonify(
                {
                    "message": "Subscription cancelled successfully. You have been downgraded to the Free plan.",
                    "endDate": end_date_display,
                    "willRenew": False,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error cancelling subscription: {str(e)}"}), 500


@billing_bp.route("/api/purchases/history", methods=["GET"])
def get_purchase_history():
    user_id = g.user_id

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    try:
        # Get credits for the user to include in the response
        credits_doc = collection.database.Credits.find_one({"user_id": user_id})
        available_credits = credits_doc.get("availableCredits", 0) if credits_doc else 0

        # Get purchase history from the database
        purchases = list(
            collection.database.Purchases.find(
                {"user_id": user_id},
                {
                    "_id": 0,
                    "date": 1,
                    "amount": 1,
                    "description": 1,
                    "status": 1,
                    "details": 1,
                },
            ).sort("date", -1)
        )

        # Format dates for JSON
        for purchase in purchases:
            if "date" in purchase:
                purchase["date"] = purchase["date"].isoformat()

        # If no purchases but user has credits, add a "system grant" entry
        if not purchases and available_credits > 0:
            purchases.append(
                {
                    "date": datetime.utcnow().isoformat(),
                    "amount": 0.00,
                    "description": f"System credit grant ({available_credits} credits)",
                    "status": "Granted",
                    "details": [],
                }
            )

        return jsonify({"purchases": purchases, "availableCredits": available_credits})
    except Exception as e:
        logger.error(f"Error fetching purchase history: {str(e)}")
        return jsonify({"error": str(e)}), 500


@billing_bp.route("/api/credits/history", methods=["GET"])
def get_credit_history():
    user_id = g.user_id

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Fetch credit history using the CreditService
        credit_history = credit_service.get_credit_history(user_id)

        # Return the credit history as JSON
        return jsonify({"creditHistory": credit_history}), 200
    except Exception as e:
        logger.error(f"Error fetching credit history: {e}")
        return jsonify({"error": "Failed to fetch credit history"}), 500
