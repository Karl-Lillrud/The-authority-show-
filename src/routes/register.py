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
    clean_name = ''.join(e for e in name if e.isalnum()).lower()
    return f"{random.randint(1000, 9999)}{clean_name}"

@register_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register/register.html")

    data = request.get_json()
    if "email" not in data or "password" not in data or "name" not in data:
        logger.warning("❌ Missing required fields")
        return jsonify({"error": "Missing required fields"}), 400

    email = data["email"].lower().strip()
    password = data["password"]
    full_name = data["name"].strip()
    hashed_password = generate_password_hash(password)
    referrer_code = data.get("referred_by", "").strip()

    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        logger.warning(f"⚠️ Email {email} already registered.")
        return jsonify({"error": "Email already registered."}), 409

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
    logger.info(f"✅ Registered user: {email} with ID {new_user_id}")

    # Skapa ett kreditdokument med 3000 krediter för alla nya användare
    existing_credits = credits_collection.find_one({"user_id": new_user_id})
    if not existing_credits:
        logger.info(f"📝 Creating credits for user: {new_user_id}")
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
        logger.info(f"✅ Credits assigned to user: {new_user_id}")
    else:
        logger.info(f"⚠️ User {new_user_id} already has credits, skipping creation.")

    # Om en referral code används, uppdatera referrer (men se till att inte användaren refererar sig själv)
    referrer = None
    if referrer_code:
        referrer = users_collection.find_one({"referral_code": referrer_code})
        if referrer and referrer["_id"] != new_user_id:
            referrer_id = referrer["_id"]
            logger.info(f"🎉 Referral detected! Updating credits for {referrer_id}")
            credits_collection.update_one(
                {"user_id": referrer_id},
                {"$inc": {"credits": 200, "referral_bonus": 200, "referrals": 1},
                 "$push": {"last_3_referrals": datetime.utcnow().isoformat()}}
            )

    return jsonify({
        "message": "Registration successful!",
        "user_id": new_user_id,
        "referral_code": referral_code,
        "redirect_url": url_for("signin_bp.signin", _external=True),
    }), 201
