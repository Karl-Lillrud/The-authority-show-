from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from backend.database.mongo_connection import collection

credits_bp = Blueprint("credits_bp", __name__)

# Constants
INITIAL_CREDITS = 3000
INVITE_CREDIT_REWARD = 200  # Bonus for referring a new user

@credits_bp.route("/credits", methods=["GET"])
def get_credits():
    email = request.args.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Fetch user from database
    user = collection.database.Users.find_one({"email": email.lower().strip()})
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    
    # Fetch user's credits
    credits = collection.database.Credits.find_one({"user_id": user_id})
    
    if not credits:
        # Initialize credits if missing
        credits = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "credits": INITIAL_CREDITS,
            "unclaimed_credits": 0,
            "referral_bonus": 0,
            "referrals": 0,
            "last_3_referrals": [],
            "vip_status": False,
            "credits_expires_at": datetime.utcnow().isoformat(),
            "episodes_published": 0,
            "streak_days": 0
        }
        collection.database.Credits.insert_one(credits)

    return jsonify({
        "user_id": user_id,
        "credits": credits.get("credits", 0),
        "unclaimed_credits": credits.get("unclaimed_credits", 0),
        "referral_bonus": credits.get("referral_bonus", 0),
        "referrals": credits.get("referrals", 0),
        "last_3_referrals": credits.get("last_3_referrals", []),
        "vip_status": credits.get("vip_status", False),
        "credits_expires_at": credits.get("credits_expires_at", "N/A"),
        "episodes_published": credits.get("episodes_published", 0),
        "streak_days": credits.get("streak_days", 0)
    }), 200


@credits_bp.route("/claim-reward", methods=["POST"])
def claim_reward():
    data = request.get_json(silent=True) or request.form.to_dict()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = collection.database.Users.find_one({"email": email.lower().strip()})
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    credits = collection.database.Credits.find_one({"user_id": user_id})

    if not credits:
        return jsonify({"error": "No credits found"}), 404

    total_claimable = credits.get("unclaimed_credits", 0) + credits.get("referral_bonus", 0)
    if total_claimable == 0:
        return jsonify({"error": "No credits available to claim"}), 400

    collection.database.Credits.update_one(
        {"user_id": user_id},
        {"$inc": {"credits": total_claimable}, "$set": {"unclaimed_credits": 0, "referral_bonus": 0}}
    )

    return jsonify({
        "message": f"{total_claimable} credits claimed!",
        "claimed_amount": total_claimable
    }), 200


@credits_bp.route("/get-referral-status", methods=["GET"])
def get_referral_status():
    email = request.args.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = collection.database.Users.find_one({"email": email.lower().strip()})
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    credits = collection.database.Credits.find_one({"user_id": user_id})

    if not credits:
        return jsonify({"error": "No credits found"}), 404

    return jsonify({
        "referrals": credits.get("referrals", 0),
        "referral_bonus": credits.get("referral_bonus", 0),
        "redirect": credits.get("referrals", 0) > 0
    }), 200

