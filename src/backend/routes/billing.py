# File: backend/routes/billing.py
from flask import Blueprint, request, jsonify, redirect, session, g
import stripe
import os
import json  # Importera json för att serialisera items
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
# get webhook secrets from environment variables
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")


@billing_bp.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    user_id = g.user_id
    data = request.get_json()
    items = data.get("items")  # Lista med produkter

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    if not items or not isinstance(items, list):
        return jsonify({"error": "Missing or invalid items list"}), 400

    try:
        line_items = []
        metadata = {
            "user_id": str(user_id),  
            "is_subscription": "false",
            "plan": "",
            "items": [],  
        }

        total_credits = 0
        total_episode_slots = 0  
        has_subscription = False
        subscription_plan = None

        
        for item in items:
            product_id = item.get("productId")
            name = item.get("name")
            item_type = item.get("type")
            price = float(item.get("price"))
            quantity = int(item.get("quantity", 1))
            credits = int(item.get("credits", 0)) if item.get("credits") else 0
            plan = item.get("plan")
            episode_slots = (
                int(item.get("episodeSlots", 0)) if item.get("episodeSlots") else 0
            )  # Get episode slots

            if item_type == "credit":
                
                line_items.append(
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {"name": name},
                            "unit_amount": int(price * 100),  # Pris i cent
                        },
                        "quantity": quantity,
                    }
                )
                total_credits += credits * quantity
                metadata["items"].append(
                    {
                        "product_id": product_id,
                        "name": name,
                        "type": "credit",
                        "credits": credits,
                        "quantity": quantity,
                    }
                )

            elif item_type == "subscription":
                
                if has_subscription:
                    return (
                        jsonify(
                            {"error": "Only one subscription allowed per checkout"}
                        ),
                        400,
                    )
                has_subscription = True
                subscription_plan = plan
                plan_prices = {"pro": 29.99, "studio": 69.00, "enterprise": 199.00}
                plan_price = plan_prices.get(plan, price)
                line_items.append(
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"{plan.capitalize()} Subscription"
                            },
                            "unit_amount": int(plan_price * 100),
                            "recurring": {"interval": "month", "interval_count": 1},
                        },
                        "quantity": 1,
                    }
                )
                metadata["items"].append(
                    {
                        "product_id": product_id,
                        "name": name,
                        "type": "subscription",
                        "plan": plan,
                        "quantity": 1,
                    }
                )

            elif item_type == "episode":
                line_items.append(
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {"name": name},
                            "unit_amount": int(price * 100),  # Price in cents
                        },
                        "quantity": quantity,
                    }
                )
                total_episode_slots += episode_slots  # Use the value from frontend
                metadata["items"].append(
                    {
                        "product_id": product_id,
                        "name": name,
                        "type": "episode",
                        "episode_slots": episode_slots,  # Store slots per item if needed
                        "quantity": quantity,
                    }
                )

        # Serialisera metadata["items"] till JSON-sträng
        metadata["items"] = json.dumps(metadata["items"])

        # Lägg till totala krediter och prenumerationsinfo i metadata
        if total_credits > 0:
            metadata["credits"] = str(total_credits)
        # Add total episode slots to metadata
        if total_episode_slots > 0:
            metadata["episode_slots"] = str(total_episode_slots)
        if has_subscription:
            metadata["is_subscription"] = "true"
            metadata["plan"] = subscription_plan or ""

        # Skapa checkout-session
        mode = "subscription" if has_subscription else "payment"
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode=mode,
            success_url=f"{os.getenv('API_BASE_URL')}/credits/success?session_id={{CHECKOUT_SESSION_ID}}&plan={subscription_plan or ''}",
            cancel_url=f"{os.getenv('API_BASE_URL')}/credits/cancel",
            metadata=metadata,
        )

        return jsonify({"sessionId": checkout_session.id})
    except Exception as e:
        logger.error(f"Stripe session creation error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@billing_bp.route("/credits/success", methods=["GET"])
def payment_success():
    # Denna route används nu primärt för omdirigering efter lyckat köp.
    # Logiken för att ge krediter/slots hanteras av webhooken.
    session_id = request.args.get("session_id")
    plan = request.args.get(
        "plan", ""
    )  # Kan fortfarande vara användbart för att visa rätt sida
    user_id = g.user_id  # Kan användas för loggning eller anpassad sida

    logger.info(
        f"User {user_id} successfully redirected after checkout session {session_id}."
    )

    if not session_id:
        return jsonify({"error": "Missing session ID"}), 400

    try:
        stripe_session = stripe.checkout.Session.retrieve(
            session_id, expand=["line_items"]
        )
        metadata = stripe_session.get("metadata", {})
        credits_to_add = int(metadata.get("credits", 0))
        # Get episode slots from metadata
        episode_slots_to_add = int(metadata.get("episode_slots", 0))
        has_subscription = metadata.get("is_subscription", "false") == "true"

        # Deserialisera items om nödvändigt
        items = json.loads(metadata.get("items", "[]")) if metadata.get("items") else []

        if plan and has_subscription:
            result, updated_credits = subscription_service.update_user_subscription(
                user_id, plan, stripe_session
            )
            logger.info(f"Subscription updated for user {user_id}: {plan}")

        if credits_to_add > 0 or episode_slots_to_add > 0:
            handle_successful_payment(stripe_session, user_id)
            if credits_to_add > 0: 
                logger.info(f"Credits processed for user {user_id}: {credits_to_add}")
            elif episode_slots_to_add > 0:
                logger.info(f"Unlocking {episode_slots_to_add} episode slots for {user_id}")

        # Omdirigera användaren till lämplig sida
        if plan:  # Om det var en prenumeration inblandad
            return redirect("/account?subscription_updated=true#settings-purchases")
        else:  # Annars till dashboard eller butik/historik
            return redirect("/dashboard?purchase_success=true")
    except Exception as e:
        logger.error(f"Payment processing error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@billing_bp.route("/credits/cancel", methods=["GET"])
def payment_cancel():
    return redirect("/account")


# --- Ny Webhook Endpoint ---
@billing_bp.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    event = None
    processed_events_collection = (
        collection.database.ProcessedStripeEvents
    )  # Ny collection för idempotency

    # --- 1. Verifiera signaturen ---
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        logger.info(f"Webhook received: Event ID={event.id}, Type={event.type}")
    except ValueError as e:
        logger.error(f"Webhook error: Invalid payload. {str(e)}")
        return jsonify(success=False, error="Invalid payload"), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook error: Invalid signature. {str(e)}")
        return jsonify(success=False, error="Invalid signature"), 400
    except Exception as e:
        logger.error(
            f"Webhook error: Generic exception during event construction. {str(e)}"
        )
        return jsonify(success=False, error=str(e)), 500

    # --- 2. Idempotency Check ---
    try:
        existing_event = processed_events_collection.find_one({"event_id": event.id})
        if existing_event:
            logger.info(f"Webhook event {event.id} already processed. Skipping.")
            return jsonify(success=True, message="Event already processed")
    except Exception as db_error:
        logger.error(
            f"Database error checking for existing event {event.id}: {db_error}"
        )
        # Fortsätt om det inte går att kolla, men logga felet
        pass  # Eller returnera 500 om detta är kritiskt

    # --- 3. Hantera specifika event-typer ---
    if event.type == "checkout.session.completed":
        session = event.data.object
        logger.info(
            f"Processing checkout.session.completed for session ID: {session.id}"
        )

        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        credits_to_add = int(metadata.get("credits", 0))
        episode_slots_to_add = int(metadata.get("episode_slots", 0))
        is_subscription = metadata.get("is_subscription", "false") == "true"
        plan = metadata.get("plan")

        if not user_id:
            logger.error(
                f"Webhook error: Missing user_id in metadata for session {session.id}"
            )
            return jsonify(
                success=True, message="Missing user_id, but acknowledged."
            )  # Return 200

        try:
            # --- 4. Utför affärslogik ---

            # Hantera prenumeration (om det är en prenumerationssession)
            # OBS: Detta anrop uppdaterar status, datum, krediter etc. baserat på planen.
            if is_subscription and plan:
                logger.info(
                    f"Webhook: Updating/Creating subscription for user {user_id}, plan {plan}. Session: {session.id}"
                )
                # Anropa funktionen som hanterar prenumerationslogiken
                # Detta kan vara den befintliga funktionen eller en ny anpassad för webhook
                subscription_service.update_user_subscription(user_id, plan, session)
                # Notera: update_user_subscription hanterar även krediterna för prenumerationen

                # Store the Stripe customer ID in the Accounts collection 
                try:
                    stripe_customer_id = session.customer
                    if stripe_customer_id:
                        # Update both by ownerId and userId to ensure we catch it
                        collection.database.Accounts.update_one(
                            {"ownerId": user_id},
                            {"$set": {"stripeCustomerId": stripe_customer_id}}
                        )
                        logger.info(f"Updated stripeCustomerId ({stripe_customer_id}) for user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to store Stripe customer ID: {str(e)}")

            # Hantera kreditpaket (om det INTE är en prenumeration eller om krediter köptes UTÖVER prenumeration)
            # Om update_user_subscription redan hanterar krediter för prenumerationer, behöver vi inte göra det igen här.
            # Vi behöver bara hantera rena kreditköp eller extra krediter köpta med prenumeration.
            # handle_successful_payment verkar designad för detta.
            if (
                credits_to_add > 0 and not is_subscription
            ):  # Bara om det är ett rent kreditköp
                logger.info(
                    f"Webhook: Handling credit purchase for user {user_id}. Credits: {credits_to_add}. Session: {session.id}"
                )
                handle_successful_payment(
                    session, user_id
                )  # Denna funktion loggar även köpet

            # Hantera episodpaket
            if episode_slots_to_add > 0:
                logger.info(
                    f"Webhook: Adding {episode_slots_to_add} episode slots for user {user_id}. Session: {session.id}"
                )
                try:
                    # TODO: Implementera och anropa funktionen för att lägga till episod-slots
                    # result = episode_service.add_episode_slots(user_id, episode_slots_to_add, session.id)
                    # if not result: raise Exception("Failed to add episode slots")
                    # Temporär loggning tills funktionen finns:
                    logger.info(
                        f"TODO: Implement episode_service.add_episode_slots({user_id}, {episode_slots_to_add}, '{session.id}')"
                    )
                    # Logga köpet av episoder separat om det inte görs i add_episode_slots
                    # purchase_data = { ... }
                    # collection.database.Purchases.insert_one(purchase_data)

                except Exception as episode_err:
                    logger.error(
                        f"Failed to add episode slots for user {user_id}, session {session.id}: {episode_err}"
                    )
                    # Fortsätt, men logga felet. Kanske markera köpet som "delvis slutfört".

            # --- 5. Spara event ID för idempotency ---
            try:
                processed_events_collection.insert_one(
                    {
                        "event_id": event.id,
                        "session_id": session.id,
                        "user_id": user_id,
                        "type": event.type,
                        "processed_at": datetime.utcnow(),
                    }
                )
                logger.info(f"Successfully marked event {event.id} as processed.")
            except Exception as db_error:
                logger.error(
                    f"Failed to save processed event {event.id} to database: {db_error}"
                )
                # Detta är ett problem, returnera 500 så Stripe försöker igen
                return (
                    jsonify(success=False, error="Failed to record event processing"),
                    500,
                )

        except Exception as processing_error:
            logger.error(
                f"Webhook processing error for session {session.id}: {processing_error}",
                exc_info=True,
            )
            # Returnera 500 så Stripe försöker skicka eventet igen
            return (
                jsonify(
                    success=False, error=f"Processing error: {str(processing_error)}"
                ),
                500,
            )

    # Keep all properly implemented handlers here...
    elif event.type == "customer.subscription.updated":
        # Keep existing customer.subscription.updated handler...
        subscription = event.data.object
        logger.info(
            f"Processing customer.subscription.updated for subscription ID: {subscription.id}"
        )
        
        # Get user_id from Stripe metadata or lookup by customer
        customer_id = subscription.customer
        account = collection.database.Accounts.find_one({"stripeCustomerId": customer_id})
        
        if not account:
            # Try finding by email through Stripe customer lookup
            try:
                customer = stripe.Customer.retrieve(customer_id)
                account = collection.database.Accounts.find_one({"email": customer.email})
            except Exception as e:
                logger.error(f"Failed to find customer: {str(e)}")
                return jsonify(success=False, error="Customer not found"), 404
        
        if account:
            user_id = account.get("userId") or account.get("ownerId")
            if not user_id:
                logger.error(f"User ID not found in account for customer {customer_id}")
                return jsonify(success=False, error="User ID not found"), 404
                
            # Check if this is an upgrade/downgrade based on price
            # Extract plan from metadata or product info
            items = subscription.items.data
            if items:
                # Get plan info from product metadata or use a pricing table mapping
                try:
                    product_id = items[0].price.product
                    product = stripe.Product.retrieve(product_id)
                    plan_name = product.metadata.get("plan") or product.name
                    
                    # Update subscription in database
                    subscription_service.update_subscription_from_webhook(
                        user_id, 
                        plan_name, 
                        subscription
                    )
                    logger.info(f"Updated subscription for user {user_id} to plan {plan_name}")
                except Exception as e:
                    logger.error(f"Failed to process subscription update: {str(e)}")
                    return jsonify(success=False, error=str(e)), 500
        else:
            logger.error(f"Account not found for customer {customer_id}")
            return jsonify(success=False, error="Account not found"), 404

    # Keep the properly implemented handlers for these events:
    elif event.type == "customer.subscription.deleted":
        # Existing complete handler...
        subscription = event.data.object
        logger.info(
            f"Processing customer.subscription.deleted for subscription ID: {subscription.id}"
        )
        
        # Get user_id using the same customer lookup logic as above
        customer_id = subscription.customer
        account = collection.database.Accounts.find_one({"stripeCustomerId": customer_id})
        
        if not account:
            try:
                customer = stripe.Customer.retrieve(customer_id)
                account = collection.database.Accounts.find_one({"email": customer.email})
            except Exception as e:
                logger.error(f"Failed to find customer: {str(e)}")
                return jsonify(success=False, error="Customer not found"), 404
        
        if account:
            user_id = account.get("userId") or account.get("ownerId")
            if not user_id:
                logger.error(f"User ID not found in account for customer {customer_id}")
                return jsonify(success=False, error="User ID not found"), 404
                
            # Update user's subscription status to FREE/cancelled
            try:
                # Update account document
                collection.database.Accounts.update_one(
                    {"_id": account["_id"]},
                    {
                        "$set": {
                            "subscriptionStatus": "cancelled",
                            "subscriptionPlan": "FREE",
                            "lastUpdated": datetime.utcnow().isoformat(),
                        }
                    },
                )
                
                # Update subscription record
                collection.database.Subscriptions.update_one(
                    {"user_id": user_id, "status": "active"},
                    {
                        "$set": {
                            "status": "cancelled",
                            "cancelled_at": datetime.utcnow().isoformat(),
                        }
                    },
                )
                
                # Reset credits to FREE plan
                from backend.services.creditService import update_subscription_credits
                update_subscription_credits(user_id, "FREE")
                
                logger.info(f"Successfully cancelled subscription for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to cancel subscription: {str(e)}")
                return jsonify(success=False, error=str(e)), 500
        else:
            logger.error(f"Account not found for customer {customer_id}")
            return jsonify(success=False, error="Account not found"), 404

    elif event.type == "invoice.paid":
        invoice = event.data.object
        
        if invoice.billing_reason == "subscription_cycle":
            logger.info(
                f"Processing invoice.paid for subscription cycle. Invoice ID: {invoice.id}, Subscription ID: {invoice.subscription}"
            )
            
            subscription_id = invoice.subscription
            
            try:
                # Get the subscription to find the customer
                subscription = stripe.Subscription.retrieve(subscription_id)
                customer_id = subscription.customer
                
                # IMPROVED CUSTOMER LOOKUP - Multiple strategies
                # 1. First try the direct lookup in Accounts
                account = collection.database.Accounts.find_one({"stripeCustomerId": customer_id})
                
                # 2. Try lookup by subscription ID in Subscriptions collection
                if not account:
                    logger.info(f"Account not found by stripeCustomerId, trying to find via subscription record...")
                    sub_record = collection.database.Subscriptions.find_one({
                        "$or": [
                            {"payment_id": subscription_id},
                            {"stripe_subscription_id": subscription_id}
                        ]
                    })
                    
                    if sub_record:
                        user_id = sub_record.get("user_id")
                        if user_id:
                            logger.info(f"Found user_id {user_id} via subscription record")
                            # Try both userId and ownerId fields
                            account = collection.database.Accounts.find_one({
                                "$or": [{"userId": user_id}, {"ownerId": user_id}]
                            })
                            
                            # Update stripeCustomerId for future lookups if we found the account
                            if account:
                                collection.database.Accounts.update_one(
                                    {"_id": account["_id"]},
                                    {"$set": {"stripeCustomerId": customer_id}}
                                )
                                logger.info(f"Updated stripeCustomerId for user {user_id}")
                
                # 3. Try by email as last resort
                if not account:
                    try:
                        customer = stripe.Customer.retrieve(customer_id)
                        logger.info(f"Looking up by email: {customer.email}")
                        account = collection.database.Accounts.find_one({"email": customer.email})
                        
                        # Update stripeCustomerId for future lookups if we found the account
                        if account:
                            collection.database.Accounts.update_one(
                                {"_id": account["_id"]},
                                {"$set": {"stripeCustomerId": customer_id}}
                            )
                            user_id = account.get("userId") or account.get("ownerId")
                            logger.info(f"Updated stripeCustomerId for user {user_id} found by email")
                            
                    except Exception as e:
                        logger.error(f"Failed to find customer by email: {str(e)}")
                
                if account:
                    user_id = account.get("userId") or account.get("ownerId")
                    
                    # Call subscription renewal handler
                    try:
                        subscription_service.handle_subscription_renewal(user_id, subscription)
                        logger.info(f"Successfully processed subscription renewal for user {user_id}")
                    except Exception as renewal_error:
                        logger.error(f"Error in subscription renewal handler: {str(renewal_error)}")
                else:
                    # Final fallback: Check all accounts for matching email pattern or username
                    logger.warning(f"Account not found by standard methods, trying advanced lookup...")
                    try:
                        customer = stripe.Customer.retrieve(customer_id)
                        if customer.email:
                            # Try a more flexible email match (case insensitive)
                            account = collection.database.Accounts.find_one(
                                {"email": {"$regex": f"^{re.escape(customer.email)}$", "$options": "i"}}
                            )
                            if account:
                                user_id = account.get("userId") or account.get("ownerId")
                                logger.info(f"Found account via case-insensitive email match for user {user_id}")
                                
                                # Update the account with the Stripe customer ID
                                collection.database.Accounts.update_one(
                                    {"_id": account["_id"]},
                                    {"$set": {"stripeCustomerId": customer_id}}
                                )
                                
                                # Process the renewal
                                subscription_service.handle_subscription_renewal(user_id, subscription)
                                logger.info(f"Successfully processed subscription renewal via advanced lookup for user {user_id}")
                                return jsonify(success=True)
                    except Exception as advanced_lookup_error:
                        logger.error(f"Advanced account lookup failed: {str(advanced_lookup_error)}")
                    
                    logger.error(f"Account not found for customer {customer_id} after all lookup attempts")
                    return jsonify(success=False, error="Account not found"), 404
                    
            except Exception as e:
                logger.error(f"Failed to process invoice payment: {str(e)}")
                return jsonify(success=False, error=str(e)), 500

    elif event.type == "invoice.payment_failed":
        # Existing complete handler...
        invoice = event.data.object
        logger.warning(
            f"Processing invoice.payment_failed. Invoice ID: {invoice.id}, Subscription ID: {invoice.subscription}"
        )
        
        subscription_id = invoice.subscription
        
        try:
            # Get the subscription to find the customer
            subscription = stripe.Subscription.retrieve(subscription_id)
            customer_id = subscription.customer
            
            # Find user by customer ID
            account = collection.database.Accounts.find_one({"stripeCustomerId": customer_id})
            if not account:
                customer = stripe.Customer.retrieve(customer_id)
                account = collection.database.Accounts.find_one({"email": customer.email})
            
            if account:
                user_id = account.get("userId") or account.get("ownerId")
                
                # Mark subscription as past_due in our database
                collection.database.Accounts.update_one(
                    {"_id": account["_id"]},
                    {
                        "$set": {
                            "subscriptionStatus": "past_due",
                            "lastUpdated": datetime.utcnow().isoformat(),
                        }
                    },
                )
                
                # Also update in Subscriptions collection
                collection.database.Subscriptions.update_one(
                    {"user_id": user_id, "status": "active"},
                    {
                        "$set": {
                            "status": "past_due",
                            "updated_at": datetime.utcnow().isoformat(),
                        }
                    },
                )
                
                # Optionally send an email notification about payment failure
                # from backend.utils.email_utils import send_email
                # send_payment_failure_email(account.get("email"))
                
                logger.info(f"Marked subscription as past_due for user {user_id}")
            else:
                logger.error(f"Account not found for customer {customer_id}")
        except Exception as e:
            logger.error(f"Failed to process failed invoice payment: {str(e)}")
            return jsonify(success=False, error=str(e)), 500

    else:
        logger.info(f"Webhook received unhandled event type: {event.type}")

    # --- 6. Bekräfta mottagandet ---
    return jsonify(success=True)


# --- End Webhook Endpoint ---


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
    try:  # Outer function try block
        # Get user ID from the current session
        user_id = g.user_id  # Get from Flask's g object
        if not user_id:
            logger.error("No user_id found in session for cancellation request")
            return jsonify({"error": "User not authenticated"}), 401
            
        # Fetch the account document first
        account = collection.database.Accounts.find_one({"userId": user_id})
        if not account:
            account = collection.database.Accounts.find_one({"ownerId": user_id})
            
        if not account:
            logger.error(f"No account found for user {user_id}")
            return jsonify({"error": "Account not found"}), 404
            
        # Get current subscription info
        subscription_status = account.get("subscriptionStatus")
        subscription_end = account.get("subscriptionEnd")
        
        # Check if already cancelled
        if subscription_status == "cancelled":
            logger.info(f"Subscription for user {user_id} is already cancelled")
            return jsonify({
                "message": "Subscription is already cancelled",
                "endDate": subscription_end,
                "willRenew": False
            }), 200

        stripe_subscription_id = None
        payment_id = None  # Initialize payment_id

        if subscription_record and subscription_record.get("payment_id"):
            payment_id = subscription_record.get("payment_id")
            if payment_id.startswith("sub_"):
                stripe_subscription_id = payment_id
                logger.info(
                    f"Found subscription ID directly in payment_id: {stripe_subscription_id}"
                )

        # Find and cancel the Stripe subscription
        try:
            # Check the local subscription record first
            subscription_record = collection.database.Subscriptions.find_one(  # Use Subscriptions collection
                {"user_id": user_id, "status": "active"}
            )

            if subscription_record and subscription_record.get("payment_id"):
                payment_id = subscription_record.get("payment_id")
                if payment_id.startswith("sub_"):
                    stripe_subscription_id = payment_id
                    logger.info(
                        f"Found subscription ID directly in local record's payment_id: {stripe_subscription_id}"
                    )
                else:
                    # If payment_id is not a sub_id, try retrieving it from the checkout session
                    logger.info(
                        f"Local record payment_id {payment_id} is not a sub_id. Attempting to retrieve from Checkout Session."
                    )
                    try:
                        checkout_session = stripe.checkout.Session.retrieve(payment_id)
                        if (
                            checkout_session
                            and hasattr(checkout_session, "subscription")
                            and checkout_session.subscription
                        ):
                            stripe_subscription_id = checkout_session.subscription
                            logger.info(
                                f"Retrieved subscription ID from Checkout Session {payment_id}: {stripe_subscription_id}"
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
                    checkout_session = stripe.checkout.Session.retrieve(payment_id)
                    if checkout_session and hasattr(checkout_session, "subscription"):
                        stripe_subscription_id = checkout_session.subscription
                        logger.info(
                            f"Retrieved subscription ID from session: {stripe_subscription_id}"
                        )
                except Exception as session_error:
                    logger.error(f"Error retrieving session: {str(session_error)}")
        except Exception as subscription_error:
            logger.error(f"Error retrieving subscription: {str(subscription_error)}")   

            # If still no ID, try finding the customer by email in Stripe
            if not stripe_subscription_id and account.get("email"):
                logger.info(
                    f"No subscription ID found yet. Searching Stripe customer by email: {account.get('email')}"
                )
                try:
                    customers = stripe.Customer.list(
                        email=account.get("email"), limit=1
                    )
                    if customers and customers.data:
                        customer_id = customers.data[0].id
                        logger.info(f"Found Stripe customer by email: {customer_id}")
                        # Look for an active subscription for this customer
                        subscriptions = stripe.Subscription.list(
                            customer=customer_id,
                            status="active",
                            limit=1,  # Fetch only one active
                        )
                        if subscriptions and subscriptions.data:
                            stripe_subscription_id = subscriptions.data[0].id
                            logger.info(
                                f"Found active subscription via customer search: {stripe_subscription_id}"
                            )
                        else:
                            logger.warning(
                                f"No active subscriptions found for customer {customer_id}"
                            )
                    else:
                        logger.warning(
                            f"No Stripe customer found for email: {account.get('email')}"
                        )
                except Exception as customer_error:
                    logger.error(
                        f"Error during Stripe customer/subscription search: {str(customer_error)}"
                    )

        except Exception as find_sub_error:
            # Catch errors during the ID finding process
            logger.error(
                f"Error occurred while trying to find the Stripe subscription ID: {str(find_sub_error)}"
            )
        # --- End of finding Stripe Subscription ID ---

        # --- Try to cancel the Stripe subscription if an ID was found ---
        if stripe_subscription_id:
            try:
                sub_check = stripe.Subscription.retrieve(stripe_subscription_id)
                if sub_check.status == "active" and not sub_check.cancel_at_period_end:
                    logger.info(
                        f"Attempting to cancel Stripe subscription {stripe_subscription_id} at period end."
                    )
                    # Set the subscription to cancel at the end of the current period
                    cancelled_subscription = stripe.Subscription.modify(
                        stripe_subscription_id, cancel_at_period_end=True
                    )
                    logger.info(
                        f"Stripe subscription {stripe_subscription_id} set to cancel at period end successfully!"
                    )
                elif sub_check.cancel_at_period_end:
                    logger.info(
                        f"Stripe subscription {stripe_subscription_id} is already set to cancel at period end."
                    )
                else:
                    logger.warning(
                        f"Stripe subscription {stripe_subscription_id} is not active (status: {sub_check.status}). Cannot modify."
                    )
            except stripe.error.StripeError as stripe_cancel_error:
                # Catch Stripe-specific errors during cancellation
                logger.error(
                    f"Stripe API error cancelling subscription {stripe_subscription_id}: {str(stripe_cancel_error)}"
                )
            except Exception as cancel_err:
                # Catch other unexpected errors during cancellation
                logger.error(
                    f"Unexpected error cancelling Stripe subscription {stripe_subscription_id}: {str(cancel_err)}"
                )
        else:
            logger.warning(
                f"No active Stripe subscription ID found for user {user_id}. Cannot cancel via Stripe API."
            )
        # --- End of cancelling Stripe subscription ---

        # --- Update Local Database Records ---
        try:
            update_query = {"userId": user_id}
            # Fallback to ownerId if userId is not the primary key in Accounts for this user
            account_check = collection.database.Accounts.find_one(update_query)
            if not account_check and account.get("ownerId") == user_id:
                update_query = {"ownerId": user_id}
                logger.info("Updating account based on ownerId instead of userId.")

            update_result = collection.database.Accounts.update_one(
                update_query,
                {
                    "$set": {
                        "subscriptionStatus": "cancelled",  # Mark as cancelled immediately in our system
                        "subscriptionPlan": "FREE",
                        "lastUpdated": datetime.utcnow().isoformat(),
                        # Decide whether to clear subscriptionEnd or keep it
                        # "subscriptionEnd": None # Example: Clear if cancelling immediately
                    }
                },
            )

            if update_result.modified_count == 0:
                if update_result.matched_count > 0:
                    logger.warning(
                        f"Account {user_id} matched but status was not updated (perhaps already cancelled?)."
                    )
                else:
                    logger.error(
                        f"Failed to update local subscription status - no account document matched query: {update_query}"
                    )
                    # Consider if this should be a hard error or just a warning

            # Update the specific subscription record in the Subscriptions collection
            subscription_update_result = collection.database.Subscriptions.update_one(  # Use Subscriptions collection
                {
                    "user_id": user_id,
                    "status": "active",
                },  # Find the active subscription record
                {
                    "$set": {
                        "status": "cancelled",  # Mark this specific record as cancelled
                        "plan": "FREE",  # Reflect the downgrade
                        "cancelled_at": datetime.utcnow().isoformat(),
                    }
                },
            )
            if subscription_update_result.modified_count == 0:
                logger.warning(
                    f"No active subscription record found in Subscriptions collection for user {user_id} to mark as cancelled."
                )

            # Update credits based on new FREE plan
            try:
                from backend.utils.subscription_access import (
                    PLAN_BENEFITS,
                )  # Ensure correct import path
                from backend.services.creditService import (
                    update_subscription_credits,
                )  # Ensure correct import path

                updated_credits = update_subscription_credits(user_id, "FREE")
                logger.info(
                    f"Updated user credits to FREE plan limits after cancellation: {updated_credits}"
                )
            except ImportError as import_err:
                logger.error(
                    f"Could not import necessary modules for credit update: {import_err}"
                )
            except Exception as credit_err:
                logger.error(f"Error updating credits after cancellation: {credit_err}")

        except Exception as db_update_error:
            logger.error(
                f"Error updating local database records after cancellation attempt: {str(db_update_error)}"
            )
            # Decide if this error should prevent a success response
        # --- End of updating Local Database Records ---

        # --- Prepare and Return Response ---
        end_date_display = None
        final_stripe_sub = None  # To store retrieved Stripe sub details

        # Try to get the period end date from Stripe if cancellation was processed
        if stripe_subscription_id:
            try:
                final_stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
                if final_stripe_sub and final_stripe_sub.cancel_at_period_end:
                    end_timestamp = final_stripe_sub.current_period_end
                    end_date = datetime.fromtimestamp(end_timestamp)
                    end_date_display = end_date.strftime("%Y-%m-%d")
                    logger.info(
                        f"Subscription access scheduled to end on: {end_date_display}"
                    )
            except Exception as e:
                logger.error(
                    f"Could not retrieve final subscription details from Stripe to confirm end date: {e}"
                )

        # Fallback to original subscriptionEnd if Stripe retrieval failed or wasn't applicable
        if not end_date_display and subscription_end:
            try:
                # Ensure subscription_end is a datetime object or valid ISO string
                if isinstance(subscription_end, str):
                    # Attempt parsing ISO format string
                    parsed_date = datetime.fromisoformat(
                        subscription_end.replace("Z", "+00:00")
                    )
                elif isinstance(subscription_end, datetime):
                    parsed_date = subscription_end
                else:
                    raise ValueError(
                        "subscription_end is not a valid date string or datetime object"
                    )
                end_date_display = parsed_date.strftime("%Y-%m-%d")
            except (ValueError, AttributeError, TypeError) as e:
                logger.error(
                    f"Error parsing original subscription end date '{subscription_end}': {e}"
                )
                end_date_display = str(
                    subscription_end
                )  # Use original value as string if parsing fails

        # Return success response, indicating cancellation is processed (or already was)
        return (
            jsonify(
                {
                    "message": "Subscription cancellation processed. If active, access will continue until the end of the current billing period.",
                    "endDate": end_date_display,  # Display when access ends, if known
                    "willRenew": False,
                }
            ),
            200,
        )
        # --- End of Prepare and Return Response ---

    except (
        Exception
    ) as e:  # Catch errors from the main function logic (auth, account fetch etc.)
        logger.error(
            f"Overall error in /cancel-subscription endpoint: {str(e)}", exc_info=True
        )
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@billing_bp.route("/api/purchases/history", methods=["GET"])
def get_purchase_history():
    user_id = g.user_id

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    try:
        credits_doc = collection.database.Credits.find_one({"user_id": user_id})
        available_credits = credits_doc.get("availableCredits", 0) if credits_doc else 0

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

        for purchase in purchases:
            if "date" in purchase:
                purchase["date"] = purchase["date"].isoformat()

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
        credit_history = credit_service.get_credit_history(user_id)
        return jsonify({"creditHistory": credit_history}), 200
    except Exception as e:
        logger.error(f"Error fetching credit history: {e}")
        return jsonify({"error": "Failed to fetch credit history"}), 500