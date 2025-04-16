# File: backend/routes/billing.py
from flask import Blueprint, request, jsonify, redirect, session, g
import stripe
import os
from backend.services.billingService import handle_successful_payment
from backend.services.subscriptionService import SubscriptionService
from backend.database.mongo_connection import collection
import logging

billing_bp = Blueprint("billing_bp", __name__)
subscription_service = SubscriptionService()
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@billing_bp.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    # Get user_id from Flask session
    user_id = g.user_id
    
    # Get data from request
    data = request.get_json()
    amount = data.get("amount")  # in dollars
    plan = data.get("plan")      # optional plan name

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
        
    if not amount:
        return jsonify({"error": "Missing amount"}), 400

    try:
        # Set product name based on whether this is a subscription or credits purchase
        product_name = f'{plan} Subscription' if plan else f'{amount} USD for Credits'
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product_name
                    },
                    'unit_amount': int(float(amount) * 100),
                    'recurring': {  # Add recurring configuration
                        'interval': 'month',
                        'interval_count': 1
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',  # Change mode from 'payment' to 'subscription'
            success_url=f"{os.getenv('API_BASE_URL')}/credits/success?session_id={{CHECKOUT_SESSION_ID}}&plan={plan or ''}",
            cancel_url=f"{os.getenv('API_BASE_URL')}/credits/cancel",
            metadata={
                'user_id': user_id,
                'is_subscription': 'true' if plan else 'false',
                'plan': plan or ''
            }
        )
        
        return jsonify({'sessionId': checkout_session.id})
    except Exception as e:
        logger.error(f"Stripe session creation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
        # Retrieve the Stripe session
        stripe_session = stripe.checkout.Session.retrieve(session_id)
        
        # Check if this is a subscription purchase or credits purchase
        if plan:
            # Handle subscription purchase
            subscription_service.update_user_subscription(user_id, plan, stripe_session)
        else:
            # Handle regular credits purchase
            handle_successful_payment(stripe_session, user_id)
            
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
