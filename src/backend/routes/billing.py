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
# Hämta webhook secret från miljövariabler
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
            "user_id": str(user_id),  # Säkerställ att user_id är sträng
            "is_subscription": "false",
            "plan": "",
            "items": [],  # Temporär lista för att samla items
        }

        total_credits = 0
        total_episode_slots = 0  # Add counter for episode slots
        has_subscription = False
        subscription_plan = None

        # Bearbeta varje produkt i items
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
                # Lägg till kreditpaket
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
                # Lägg till prenumeration
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

    # Omdirigera användaren till lämplig sida
    if plan:  # Om det var en prenumeration inblandad
        return redirect("/account?subscription_updated=true#settings-purchases")
    else:  # Annars till dashboard eller butik/historik
        return redirect("/dashboard?purchase_success=true")


@billing_bp.route("/credits/cancel", methods=["GET"])
def payment_cancel():
    return redirect("/account")


# --- Ny Webhook Endpoint ---
@billing_bp.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        logger.info(f"Webhook received: Event ID={event.id}, Type={event.type}")
    except ValueError as e:
        # Invalid payload
        logger.error(f"Webhook error: Invalid payload. {str(e)}")
        return jsonify(success=False, error="Invalid payload"), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Webhook error: Invalid signature. {str(e)}")
        return jsonify(success=False, error="Invalid signature"), 400
    except Exception as e:
        logger.error(f"Webhook error: Generic exception. {str(e)}")
        return jsonify(success=False, error=str(e)), 500

    # Hantera eventet checkout.session.completed
    if event.type == "checkout.session.completed":
        session = event.data.object  # session är ett stripe.checkout.Session objekt
        logger.info(
            f"Processing checkout.session.completed for session ID: {session.id}"
        )

        # Hämta metadata
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
            # Returnera 200 ändå så Stripe inte försöker igen för detta specifika fel
            return jsonify(success=True, message="Missing user_id, but acknowledged.")

        try:
            # TODO: Lägg till idempotency check här - har denna session.id redan bearbetats?
            # Ex: if purchase_already_processed(session.id): return jsonify(success=True)

            # Hantera prenumeration (om det finns)
            if is_subscription and plan:
                # Använd subscriptionService för att uppdatera/skapa prenumeration
                # Notera: Stripe skickar separata events för prenumerationer (invoice.paid etc.)
                # Det kan vara bättre att hantera prenumerationsaktivering där.
                # Här kan vi dock logga eller sätta en initial flagga.
                logger.info(
                    f"Webhook: Subscription purchase detected for user {user_id}, plan {plan}. Session: {session.id}"
                )
                # subscription_service.handle_subscription_creation(user_id, plan, session) # Exempel

            # Hantera kreditpaket
            if credits_to_add > 0:
                logger.info(
                    f"Webhook: Adding {credits_to_add} credits for user {user_id}. Session: {session.id}"
                )
                # Använd billingService eller creditService för att lägga till krediter
                handle_successful_payment(
                    session, user_id
                )  # Använder befintlig funktion

            # Hantera episodpaket
            if episode_slots_to_add > 0:
                logger.info(
                    f"Webhook: Adding {episode_slots_to_add} episode slots for user {user_id}. Session: {session.id}"
                )
                # TODO: Anropa funktionen för att lägga till episod-slots
                # episode_service.add_episode_slots(user_id, episode_slots_to_add, session.id) # Exempel, skicka med session.id för idempotency/spårning

            # TODO: Spara information om köpet (t.ex. i Purchases collection) om det inte görs i handle_successful_payment

        except Exception as e:
            logger.error(f"Webhook processing error for session {session.id}: {str(e)}")
            # Returnera 500 så Stripe försöker skicka eventet igen
            return jsonify(success=False, error=f"Processing error: {str(e)}"), 500

    # Lägg till hantering för andra event-typer vid behov
    # elif event.type == 'invoice.paid':
    #    # Hantera återkommande prenumerationsbetalningar
    #    pass
    # elif event.type == 'invoice.payment_failed':
    #    # Hantera misslyckade betalningar
    #    pass

    else:
        logger.info(f"Webhook received unhandled event type: {event.type}")

    # Bekräfta mottagandet till Stripe
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
    try:
        flask_session = session
        user_id = flask_session.get("user_id")
        logger.info(f"Cancel subscription requested for user_id: {user_id}")

        if not user_id:
            user_id = getattr(g, "user_id", None)
            logger.info(f"Trying g.user_id instead: {user_id}")

        if not user_id:
            logger.error("Cancellation failed: User not authenticated")
            return jsonify({"error": "User not authenticated"}), 401

        account = collection.database.Accounts.find_one({"userId": user_id})
        if not account:
            logger.info(f"Account not found with userId, trying with ownerId...")
            account = collection.database.Accounts.find_one({"ownerId": user_id})

        if not account:
            logger.error(f"Cancellation failed: Account not found for user {user_id}")
            return jsonify({"error": "Account not found"}), 404

        subscription_end = account.get("subscriptionEnd")
        if account.get("subscriptionStatus") == "cancelled":
            logger.info(f"Subscription already cancelled for user {user_id}")
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


        stripe_subscription_id = None
        subscription_record = collection.database.subscriptions_collection.find_one(
            {"user_id": user_id, "status": "active"}
        )

        if subscription_record and subscription_record.get("payment_id"):
            payment_id = subscription_record.get("payment_id")
            if payment_id.startswith("sub_"):
                stripe_subscription_id = payment_id
                logger.info(
                    f"Found subscription ID directly in payment_id: {stripe_subscription_id}"
                )
            else:

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
                    checkout_session = stripe.checkout.Session.retrieve(payment_id)
                    if checkout_session and hasattr(checkout_session, "subscription"):
                        stripe_subscription_id = checkout_session.subscription
                        logger.info(
                            f"Retrieved subscription ID from session: {stripe_subscription_id}"
                        )
                except Exception as session_error:
                    logger.error(f"Error retrieving session: {str(session_error)}")

        if not stripe_subscription_id:
            if account.get("email"):
                try:
                    customers = stripe.Customer.list(
                        email=account.get("email"), limit=1
                    )
                    if customers and customers.data:
                        customer_id = customers.data[0].id
                        logger.info(f"Found Stripe customer by email: {customer_id}")
                        subscriptions = stripe.Subscription.list(
                            customer=customer_id, status="active", limit=5
                        )
                        if subscriptions and subscriptions.data:
                            stripe_subscription_id = subscriptions.data[0].id
                            logger.info(
                                f"Selected subscription for cancellation: {stripe_subscription_id}"
                            )
                except Exception as customer_error:
                    logger.error(
                        f"Error with Stripe customer operations: {str(customer_error)}"
                    )

        if stripe_subscription_id:
            try:
                sub_check = stripe.Subscription.retrieve(stripe_subscription_id)
                if sub_check.status == "active" and not sub_check.cancel_at_period_end:
                    cancelled_subscription = stripe.Subscription.modify(
                        stripe_subscription_id, cancel_at_period_end=True
                    )
                    logger.info(
                        f"Stripe subscription {stripe_subscription_id} cancelled successfully!"
                    )
            except stripe.error.StripeError as stripe_specific_error:
                logger.error(
                    f"Stripe API error cancelling subscription: {str(stripe_specific_error)}"
                )

        update_query = {"userId": user_id}
        if "ownerId" in account and not account.get("userId"):
            update_query = {"ownerId": user_id}

        update_result = collection.database.Accounts.update_one(
            update_query,
            {
                "$set": {
                    "subscriptionStatus": "cancelled",
                    "subscriptionPlan": "FREE",
                    "lastUpdated": datetime.utcnow().isoformat(),
                }
            },
        )

        if update_result.modified_count == 0 and update_result.matched_count == 0:
            logger.error(f"Failed to update subscription status - no document matched")
            return jsonify({"error": "Failed to update subscription status"}), 500


        subscription_result = collection.database.subscriptions_collection.update_one(

            {"user_id": user_id, "status": "active"},
            {
                "$set": {
                    "status": "cancelled",
                    "plan": "FREE",
                    "cancelled_at": datetime.utcnow().isoformat(),
                }
            },
        )

        try:
            from backend.utils.subscription_access import PLAN_BENEFITS
            from backend.services.creditService import update_subscription_credits

            updated_credits = update_subscription_credits(user_id, "FREE")
            logger.info(
                f"Updated user credits to FREE plan after cancellation: {updated_credits}"
            )
        except Exception as credit_err:
            logger.error(f"Error updating credits after cancellation: {credit_err}")

        end_date_display = None
        if subscription_end:
            try:
                end_date = datetime.fromisoformat(
                    subscription_end.replace("Z", "+00:00")
                )
                end_date_display = end_date.strftime("%Y-%m-%d")
            except (ValueError, AttributeError) as e:
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
