from flask import Blueprint, request, jsonify, render_template, url_for
from werkzeug.security import generate_password_hash
from datetime import datetime
import uuid
import secrets, string
import logging
from backend.database.mongo_connection import collection

# Ställ in logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

register_bp = Blueprint("register_bp", __name__)

# Konstanter
INITIAL_CREDITS = 3000
INVITE_CREDIT_REWARD = 200  # Bonus per enskild referral

def generate_referral_code(email):
    alphabet = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(alphabet) for _ in range(6))
    logger.debug(f"Generated referral code {code} for email {email}")
    return code

@register_bp.route("/register", methods=["GET", "POST"])
def register():
    logger.debug("Entered register endpoint")
    if request.method == "GET":
        referral = request.args.get("referral", "").strip()
        logger.debug(f"GET request with referral: {referral}")
        return render_template("register/register.html", referral=referral)

    data = request.get_json(silent=True) or request.form.to_dict()
    logger.debug(f"POST data received: {data}")
    if not data or "email" not in data or "password" not in data:
        logger.error("Missing required fields: email and password")
        return jsonify({"error": "Missing required fields (email and password)"}), 400

    email = data["email"].lower().strip()
    password = data["password"]
    hashed_password = generate_password_hash(password)
    logger.debug(f"Email: {email}, password hash generated.")

    existing_user = collection.database.Users.find_one({"email": email})
    if existing_user:
        logger.error(f"User already exists with email: {email}")
        return jsonify({"error": "User already registered with this email"}), 409

    # Hämta referral-kod från data eller query-parameter
    referrer_code = data.get("referred_by", "").strip() or request.args.get("referral", "").strip()
    logger.debug(f"Referral code from request: {referrer_code}")
    referral_code = generate_referral_code(email)

    new_user_id = str(uuid.uuid4())
    user_document = {
        "_id": new_user_id,
        "email": email,
        "passwordHash": hashed_password,
        "createdAt": datetime.utcnow().isoformat(),
        "referral_code": referral_code,
        "referred_by": referrer_code if referrer_code else None
    }
    logger.debug(f"Inserting new user: {user_document}")
    collection.database.Users.insert_one(user_document)

    credits_document = {
        "_id": str(uuid.uuid4()),
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
    logger.debug(f"Inserting credits document: {credits_document}")
    existing_credits = collection.database.Credits.find_one({"user_id": new_user_id})
    if not existing_credits:
        collection.database.Credits.insert_one(credits_document)

    # Om referral-kod angavs, uppdatera referrarens credits
    if referrer_code:
        logger.debug(f"Referral code provided: {referrer_code}")
        referrer = collection.database.Users.find_one({"referral_code": referrer_code})
        logger.debug(f"Found referrer: {referrer}")
        if referrer:
            if referrer["_id"] == new_user_id:
                logger.error("User attempted to refer themselves")
                return jsonify({"error": "User cannot refer themselves."}), 400
            referrer_id = referrer["_id"]
            # Öka per referral
            collection.database.Credits.update_one(
                {"user_id": referrer_id},
                {
                    "$inc": {"credits": INVITE_CREDIT_REWARD, "referrals": 1, "referral_bonus": INVITE_CREDIT_REWARD}
                },
                upsert=True
            )
            logger.debug(f"Incremented referral stats for user_id {referrer_id}")

            # Hämta uppdaterat dokument för att kontrollera referrals-count
            ref_credits = collection.database.Credits.find_one({"user_id": referrer_id})
            logger.debug(f"Referrer credits document after update: {ref_credits}")
            if ref_credits.get("referrals", 0) == 3 and not ref_credits.get("milestone_awarded", False):
                # När 3 referrals uppnåtts, ge extra bonus på 1500 credits
                collection.database.Credits.update_one(
                    {"user_id": referrer_id},
                    {
                        "$inc": {"credits": 1500},
                        "$set": {"milestone_awarded": True}
                    }
                )
                logger.info(f"Milestone bonus awarded: 1500 credits to user_id {referrer_id}, result: {milestone_result.raw_result}")
        else:
            logger.error(f"Referrer with code {referrer_code} not found.")

    # Skapa konto i Accounts-samlingen
    account_data = {
        "userId": new_user_id,
        "email": email,
        "companyName": data.get("companyName", ""),
        "isCompany": data.get("isCompany", False),
        "ownerId": new_user_id,
    }
    logger.debug(f"Inserting account data: {account_data}")
    collection.database.Accounts.insert_one(account_data)

    logger.info(f"User registration successful for {email} with user_id {new_user_id} and referral_code {referral_code}")
    return jsonify({
        "message": "Registration successful!",
        "user_id": new_user_id,
        "referral_code": referral_code,
        "redirect_url": url_for("signin_bp.signin", _external=True)
    }), 201
