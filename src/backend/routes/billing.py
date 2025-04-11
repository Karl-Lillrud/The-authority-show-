# File: backend/routes/billing.py
from flask import Blueprint, request, jsonify, redirect
import stripe
import os
from backend.services.billingService import handle_successful_payment
from backend.database.mongo_connection import collection

billing_bp = Blueprint("billing_bp", __name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@billing_bp.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json()
    user_id = data.get("user_id")
    amount = data.get("amount")  # in dollars

    if not user_id or not amount:
        return jsonify({"error": "Missing user_id or amount"}), 400

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{amount} USD for Credits'
                    },
                    'unit_amount': int(amount * 100),  # Stripe takes cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{os.getenv('APP_BASE_URL')}/credits/success?session_id={{CHECKOUT_SESSION_ID}}&user_id={user_id}",
            cancel_url=f"{os.getenv('APP_BASE_URL')}/credits/cancel",
        )
        return jsonify({'sessionId': session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@billing_bp.route("/credits/success", methods=["GET"])
def payment_success():
    session_id = request.args.get("session_id")
    user_id = request.args.get("user_id")

    if not session_id or not user_id:
        return jsonify({"error": "Missing session ID or user ID"}), 400

    session = stripe.checkout.Session.retrieve(session_id)

    try:
        handle_successful_payment(session, user_id)
        return redirect("/dashboard")  # or dashboard
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@billing_bp.route("/credits/cancel", methods=["GET"])
def payment_cancel():
    return redirect("/account")
