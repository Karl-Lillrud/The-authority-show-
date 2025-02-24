from flask import Blueprint, request, jsonify, url_for, render_template
from werkzeug.security import generate_password_hash
from datetime import datetime
import uuid
import random
from database.mongo_connection import users_collection, credits_collection
import logging

register_bp = Blueprint("register_bp", __name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_referral_code(name):
    # Remove non-alphanumeric characters and prepend a random 4-digit number.
    clean_name = ''.join(e for e in name if e.isalnum()).lower()
    return f"{random.randint(1000, 9999)}{clean_name}"

@register_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        # Pass referral code from URL query to the registration form
        referral = request.args.get("referral", "").strip()
        logger.info(f"Referral code from query: {referral}")
        return render_template("register/register.html", referral=referral)

    # Accept data either as JSON or form data
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data or "email" not in data or "password" not in data or "name" not in data:
        logger.warning("Missing required fields")
        return jsonify({"error": "Missing required fields"}), 400

    email = data["email"].lower().strip()
    password = data["password"]
    full_name = data["name"].strip()
    hashed_password = generate_password_hash(password)

    # Try to get referral code from POST data ("referred_by") or fallback to URL query parameter "referral"
    referrer_code = data.get("referred_by", "").strip() or request.args.get("referral", "").strip()
    logger.info(f"Referrer code from POST/URL: {referrer_code}")

    # Check if user already exists
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        logger.warning(f"Email {email} already registered.")
        return jsonify({"error": "Email already registered."}), 409

    # Generate unique user id and referral code for new user
    new_user_id = str(uuid.uuid4())
    referral_code = generate_referral_code(full_name)

    user_document = {
        "_id": new_user_id,
        "email": email,
        "passwordHash": hashed_password,
        "full_name": full_name,
        "createdAt": datetime.utcnow().isoformat(),
        "referral_code": referral_code,
        "referred_by": referrer_code if referrer_code else None
    }

    users_collection.insert_one(user_document)
    logger.info(f"Registered user: {email} with ID {new_user_id}")

    # Create credits document for the new user (3000 starting points/credits)
    if not credits_collection.find_one({"user_id": new_user_id}):
        credits_document = {
            "_id": str(uuid.uuid4()),
            "user_id": new_user_id,
            "credits": 3000,
            "unclaimed_credits": 0,
            "referral_bonus": 0,
            "referrals": 0,
            "last_3_referrals": [],
            "vip_status": False,
            "credits_expires_at": datetime.utcnow().isoformat(),
            "episodes_published": 0,
            "streak_days": 0
        }
        credits_collection.insert_one(credits_document)
        logger.info(f"Credits assigned to user: {new_user_id}")
    else:
        logger.info(f"User {new_user_id} already has credits, skipping creation.")

    # If a valid referral code was provided, update the referrer's credits
    if referrer_code:
        referrer = users_collection.find_one({"referral_code": referrer_code})
        if referrer:
            if referrer["_id"] == new_user_id:
                logger.warning("User attempted to refer themselves. Ignoring referral bonus.")
            else:
                referrer_id = referrer["_id"]
                logger.info(f"Referral detected! Updating credits for referrer {referrer_id}")
                # Ensure referrer has a credits document; create one if missing
                if not credits_collection.find_one({"user_id": referrer_id}):
                    new_ref_credits = {
                        "_id": str(uuid.uuid4()),
                        "user_id": referrer_id,
                        "credits": 3000,  # starting credits for referrer
                        "unclaimed_credits": 0,
                        "referral_bonus": 0,
                        "referrals": 0,
                        "last_3_referrals": [],
                        "vip_status": False,
                        "credits_expires_at": datetime.utcnow().isoformat(),
                        "episodes_published": 0,
                        "streak_days": 0
                    }
                    credits_collection.insert_one(new_ref_credits)
                    logger.info(f"Created credits document for referrer: {referrer_id}")

                # Update referrer's credits: add bonus (example bonus: 200 credits)
                result = credits_collection.update_one(
                    {"user_id": referrer_id},
                    {"$inc": {"credits": 200, "referral_bonus": 200, "referrals": 1},
                     "$push": {"last_3_referrals": datetime.utcnow().isoformat()}}
                )
                logger.info(f"Referrer {referrer_id} updated: Matched {result.matched_count}, Modified {result.modified_count}")
        else:
            logger.warning(f"Referral code '{referrer_code}' not found.")

    return jsonify({
        "message": "Registration successful!",
        "user_id": new_user_id,
        "referral_code": referral_code,
        "redirect_url": url_for("signin_bp.signin", _external=True)
    }), 201

