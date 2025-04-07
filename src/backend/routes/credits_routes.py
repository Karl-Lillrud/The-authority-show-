from flask import Blueprint, request, jsonify
from backend.services.creditService import get_user_credits, consume_credits
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

