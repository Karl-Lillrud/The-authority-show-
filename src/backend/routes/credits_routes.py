from flask import Blueprint, request, jsonify, g, redirect, url_for
from backend.services.creditService import get_store_credits, consume_credits
from backend.database.mongo_connection import credits

credits_bp = Blueprint("credits_bp", __name__)


@credits_bp.route("/credits/<user_id>", methods=["GET"])
def get_credits(user_id):
    try:
        credits = get_store_credits(user_id)  # Updated method name
        if not credits:
            return jsonify({"error": "No credits found"}), 404
        return jsonify(credits)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@credits_bp.route("/credits/consume", methods=["POST"])
def consume():
    if not g.user_id:
        return redirect(url_for("auth_bp.signin"))
    data = request.get_json()
    user_id = data.get("user_id")
    feature = data.get("feature")
    try:
        result = consume_credits(user_id, feature)
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@credits_bp.route("/api/credits", methods=["GET"])
def get_available_credits():
    from backend.services.creditManagement import CreditService

    # Get user_id from session
    user_id = g.user_id

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    try:
        # Get credits directly from the database first
        credit_doc = credits.find_one({"user_id": user_id})

        if not credit_doc:
            # No credits found - return zeros
            return jsonify({"availableCredits": 0, "subCredits": 0, "storeCredits": 0})

        # Handle both old and new credit formats
        if "subCredits" in credit_doc or "storeCredits" in credit_doc:
            # New credit format
            sub_credits = credit_doc.get("subCredits", 0)
            store_credits = credit_doc.get("storeCredits", 0)
            # If sub_credits is 0 but availableCredits > 0, treat initial credits as subCredits
            if sub_credits == 0 and credit_doc.get("availableCredits", 0) > 0:
                sub_credits = credit_doc.get("availableCredits", 0)
            available = sub_credits + store_credits
        else:
            # Old credit format - use availableCredits directly
            available = credit_doc.get("availableCredits", 0)
            sub_credits = available  # Assume all are subscription credits
            store_credits = 0

        # Return all values to ensure UI has complete data
        response_data = {
            "availableCredits": available,
            "subCredits": sub_credits,
            "storeCredits": store_credits,
        }
        print(f"DEBUG - Credits for user {user_id}: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching credits: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch credits"}), 500


@credits_bp.route("/api/credits/check", methods=["GET"])
def check_store_credits():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User id is required."}), 400

    credit_doc = credits.find_one({"user_id": user_id})
    if not credit_doc:
        return jsonify({"error": "Credits not found."}), 404

    available = credit_doc.get("availableCredits", 0)
    return jsonify({"availableCredits": available})
