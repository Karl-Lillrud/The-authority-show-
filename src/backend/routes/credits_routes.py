from flask import Blueprint, request, jsonify, g
from backend.services.creditService import get_user_credits, consume_credits
from backend.database.mongo_connection import credits

credits_bp = Blueprint("credits_bp", __name__)

@credits_bp.route("/credits/<user_id>", methods=["GET"])
def get_credits(user_id):
    try:
        credits = get_user_credits(user_id)
        if not credits:
            return jsonify({"error": "No credits found"}), 404
        return jsonify(credits)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@credits_bp.route("/credits/consume", methods=["POST"])
def consume():
    data = request.get_json()
    user_id = data.get("user_id")
    feature = data.get("feature")
    try:
        result = consume_credits(user_id, feature)
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@credits_bp.route('/api/credits', methods=['GET'])
def get_available_credits():
    from backend.services.creditManagement import CreditService
    
    # Get user_id from session
    user_id = g.user_id
    
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    # Use CreditService which already handles the calculation of availableCredits
    credit_service = CreditService()
    credits_data = credit_service.get_user_credits(user_id)
    
    if not credits_data:
        return jsonify({"availableCredits": 0})  # Return 0 if no credits found
    
    # CreditService already calculates availableCredits from pmCredits + userCredits
    return jsonify({
        "availableCredits": credits_data.get("availableCredits", 0),
        "pmCredits": credits_data.get("pmCredits", 0),
        "userCredits": credits_data.get("userCredits", 0)
    })

@credits_bp.route('/api/credits/check', methods=['GET'])
def check_user_credits():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User id is required."}), 400

    credit_doc = credits.find_one({"user_id": user_id})
    if not credit_doc:
        return jsonify({"error": "Credits not found."}), 404

    available = credit_doc.get("availableCredits", 0)
    return jsonify({"availableCredits": available})