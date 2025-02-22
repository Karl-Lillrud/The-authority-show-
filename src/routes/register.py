
from flask import Blueprint, request, jsonify, url_for, render_template
from werkzeug.security import generate_password_hash
from datetime import datetime
import uuid
import random
import string
from database.mongo_connection import users_collection, credits_collection

import logging

register_bp = Blueprint("register_bp", __name__)

# 📌 Konfigurera loggning
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_referral_code(name):
    """Genererar en unik referral-kod där slumpmässiga siffror kommer först"""
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

    # Kolla om användaren redan finns
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        logger.warning(f"⚠️ Email {email} already registered.")
        return jsonify({"error": "Email already registered."}), 409

    # ✅ Skapa nytt user-dokument
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

    users_collection.insert_one(user_document)  # Lägg till användaren i MongoDB
    logger.info(f"✅ Användare registrerad: {email} med ID {new_user_id}")

    # ✅ Kontrollera om användaren redan har en credits-post innan vi skapar en ny
    existing_credits = credits_collection.find_one({"user_id": new_user_id})
    if not existing_credits:
        logger.info(f"📝 Skapar credits för användare: {new_user_id}")
        credits_document = {
            "_id": str(uuid.uuid4()),
            "user_id": new_user_id,
            "credits": 3000,  # Startkrediter
            "unclaimed_credits": 0,
            "referral_bonus": 0,
            "referrals": 0,
            "last_3_referrals": [],
            "vip_status": False,
            "credits_expires_at": datetime.utcnow().isoformat()
        }
        credits_collection.insert_one(credits_document)
        logger.info(f"✅ Credits tilldelade till användare: {new_user_id}")
    else:
        logger.info(f"⚠️ Användaren {new_user_id} har redan en credits-post, hoppar över.")

    # ✅ Om referral-kod används, uppdatera den som refererade
    if referrer_code:
        referrer = users_collection.find_one({"referral_code": referrer_code})
        if referrer:
            referrer_id = str(referrer["_id"])
            logger.info(f"🎉 Referral upptäckt! Uppdaterar credits för {referrer_id}")
            credits_collection.update_one(
                {"user_id": referrer_id},
                {"$inc": {"referral_bonus": 200, "referrals": 1},
                "$push": {"last_3_referrals": datetime.utcnow().isoformat()}}
            )

    return jsonify({
        "message": "Registration successful!",
        "user_id": new_user_id,
        "referral_code": referral_code,
        "redirect_url": url_for("signin_bp.signin", _external=True),
    }), 201
