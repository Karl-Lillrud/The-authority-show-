# File: backend/routes/billing.py
from flask import Blueprint, request, jsonify, redirect, session, g
import stripe
import os
from backend.services.billingService import handle_successful_payment
from backend.database.mongo_connection import collection

billing_bp = Blueprint("billing_bp", __name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@billing_bp.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    # Get user_id from Flask session instead of request body
    user_id = g.user_id
    
    # Get amount from request data
    data = request.get_json()
    amount = data.get("amount")  # in dollars

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
        
    if not amount:
        return jsonify({"error": "Missing amount"}), 400

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{amount} USD for Credits'
                    },
                    'unit_amount': int(float(amount) * 100),  # Stripe takes cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{os.getenv('API_BASE_URL')}/credits/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('API_BASE_URL')}/credits/cancel",
        )
        return jsonify({'sessionId': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@billing_bp.route("/credits/success", methods=["GET"])
def payment_success():
    session_id = request.args.get("session_id")
    # Get user_id from Flask session instead of query parameter
    user_id = g.user_id

    if not session_id:
        return jsonify({"error": "Missing session ID"}), 400
        
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    try:
        stripe_session = stripe.checkout.Session.retrieve(session_id)
        handle_successful_payment(stripe_session, user_id)
        return redirect("/dashboard")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@billing_bp.route("/credits/cancel", methods=["GET"])
def payment_cancel():
    return redirect("/account")
