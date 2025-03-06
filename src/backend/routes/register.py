from flask import Blueprint, request, jsonify, render_template, url_for
from werkzeug.security import generate_password_hash
from datetime import datetime
import uuid
import secrets, string

import random
from backend.database.mongo_connection import collection

register_bp = Blueprint("register_bp", __name__)

# Constants
INITIAL_CREDITS = 3000
INVITE_CREDIT_REWARD = 200  # Bonus for referring a new user

def generate_referral_code(email):
    # Generate an 6-character referral code using uppercase letters and digits
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(6))

@register_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        referral = request.args.get("referral", "").strip()
        return render_template("register/register.html", referral=referral)

    # Handle POST request (user registration)
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Missing required fields (email and password)"}), 400

    email = data["email"].lower().strip()
    password = data["password"]
    hashed_password = generate_password_hash(password)

    # Check if email already exists in the database
    existing_user = collection.database.Users.find_one({"email": email})
    if existing_user:
        return jsonify({"error": "User already registered with this email"}), 409

    # Get referral code
    referrer_code = data.get("referred_by", "").strip() or request.args.get("referral", "").strip()
    referral_code = generate_referral_code(email)

    # Create User document
    new_user_id = str(uuid.uuid4())
    user_document = {
        "_id": new_user_id,
        "email": email,
        "passwordHash": hashed_password,
        "createdAt": datetime.utcnow().isoformat(),
        "referral_code": referral_code,
        "referred_by": referrer_code if referrer_code else None
    }

    # Insert user into Users collection
    collection.database.Users.insert_one(user_document)

    # Create Credits document for the new user
    credits_document = {
        "_id": str(uuid.uuid4()),  # Use a separate UUID for credits
        "user_id": new_user_id,
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

    # Check if user already has a credits document
    existing_credits = collection.database.Credits.find_one({"user_id": new_user_id})
    if not existing_credits:
        collection.database.Credits.insert_one(credits_document)

    # Award bonus credits if the user was referred by someone
    if referrer_code:
       referrer = collection.database.Users.find_one({"referral_code": referrer_code})
       if referrer:
            if referrer["_id"] == new_user_id:
               return jsonify({"error": "User cannot refer themselves."}), 400
            referrer_id = referrer["_id"]
            collection.database.Credits.update_one(
            {"user_id": referrer_id},
            {
                "$inc": {"credits": INVITE_CREDIT_REWARD, "referrals": 1, "referral_bonus": INVITE_CREDIT_REWARD},
                "$setOnInsert": {"user_id": referrer_id}
            },
            upsert=True
        )


    # Create account entry in the Accounts collection
    account_data = {
        "userId": new_user_id,
        "email": email,
        "companyName": data.get("companyName", ""),
        "isCompany": data.get("isCompany", False),
        "ownerId": new_user_id,
    }
    # Directly insert into the Accounts collection
    collection.database.Accounts.insert_one(account_data)

    # Return success response
    return jsonify({
        "message": "Registration successful!",
        "user_id": new_user_id,
        "referral_code": referral_code,
        "redirect_url": url_for("signin_bp.signin", _external=True)
    }), 201
