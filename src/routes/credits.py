from flask import Blueprint, jsonify, request, Response, stream_with_context
from database.mongo_connection import users_collection, credits_collection
import smtplib
import os
import ssl
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bson import ObjectId
from datetime import datetime

credits_bp = Blueprint('credits_bp', __name__)

# 📌 Hämtar en användares credits
@credits_bp.route('/credits/<user_id>', methods=['GET'])
def get_credits(user_id):
    try:
        credits = credits_collection.find_one({"user_id": user_id})

        if not credits:
            return jsonify({"error": "No credits found"}), 404

        return jsonify({
            "user_id": user_id,
            "credits": credits.get("credits", 0),
            "credits_expires_at": credits.get("credits_expires_at", "N/A")
        })
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# 📌 Hanterar anspråk på belöningar
@credits_bp.route("/claim-reward", methods=["POST"])
def claim_reward():
    try:
        data = request.json
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        credits = credits_collection.find_one({"user_id": user_id})

        if not credits:
            return jsonify({"error": "No credits found"}), 404

        total_claimable = credits.get("unclaimed_credits", 0) + credits.get("referral_bonus", 0)

        if total_claimable == 0:
            return jsonify({"error": "No credits available to claim"}), 400

        credits_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"credits": total_claimable},
             "$set": {"unclaimed_credits": 0, "referral_bonus": 0}}
        )

        return jsonify({"success": True, "message": f"{total_claimable} credits claimed!"}), 200

    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500


# 📌 Hämtar användarens progressdata
@credits_bp.route('/user-progress/<user_id>', methods=['GET'])
def user_progress(user_id):
    try:
        credits = credits_collection.find_one({"user_id": user_id})

        if not credits:
            return jsonify({"error": "No credits found"}), 404

        return jsonify({
            "user_id": user_id,
            "credits": credits.get("credits", 0),
            "unclaimed_credits": credits.get("unclaimed_credits", 0),
            "referral_bonus": credits.get("referral_bonus", 0),
            "referrals": credits.get("referrals", 0),
            "episodes_published": credits.get("episodes_published", 0),
            "streak_days": credits.get("streak_days", 0),
            "last_3_referrals": credits.get("last_3_referrals", [])
        })

    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500


# 📌 Skickar inbjudningar via e-post
def send_email(to_email, subject, message):
    try:
        msg = MIMEMultipart()
        msg["From"] = os.getenv("EMAIL_USER")
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT", 587))) as server:
            server.starttls(context=context)
            server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
            server.sendmail(os.getenv("EMAIL_USER"), to_email, msg.as_string())

        return True
    except Exception:
        return False


@credits_bp.route("/send-invite", methods=["POST"])
def send_invite():
    data = request.json
    friend_email = data.get("email")
    referral_code = data.get("referralCode")

    if not friend_email or not referral_code:
        return jsonify({"error": "Missing email or referral code"}), 400

    referrer = users_collection.find_one({"referral_code": referral_code})

    if not referrer:
        return jsonify({"error": "Invalid referral code"}), 404

    sender_email = referrer["email"]

    subject = f"🎉 {sender_email} has invited you to PodManager!"
    message = f"""
    <h2>🚀 {sender_email} has invited you to PodManager!</h2>
    <p>Hey! <b>{sender_email}</b> has invited you to join PodManager. Sign up now and get <b>3,000 free credits</b>!</p>
    <a href="http://127.0.0.1:8000/register?referral={referral_code}">
        Register Now
    </a>
    """

    success = send_email(friend_email, subject, message)

    if success:
        return jsonify({"success": True, "message": "Invite sent!"}), 200
    else:
        return jsonify({"error": "Failed to send invite"}), 500


# 📌 Hämtar referral-status
@credits_bp.route("/get-referral-status/<user_id>", methods=["GET"])
def get_referral_status(user_id):
    try:
        credits = credits_collection.find_one({"user_id": user_id})

        if not credits:
            return jsonify({"error": "No credits found"}), 404

        return jsonify({
            "success": True,
            "referrals": credits.get("referrals", 0),
            "redirect": credits.get("referrals", 0) > 0
        })

    except Exception as e:
        return jsonify({"error": "Database error"}), 500


# 📌 Streamar referral-uppdateringar i realtid
# 📌 Streamar referral-uppdateringar i realtid
@credits_bp.route("/stream-referral-updates", methods=["GET"])
def stream_referral_updates():
    email = request.args.get("email")
    
    if not email:
        return jsonify(success=False, error="No email provided"), 400

    return Response(stream_with_context(event_stream(email)), content_type="text/event-stream")

def event_stream(email):
    last_referral_bonus = get_referral_bonus(email)

    while True:
        time.sleep(5)  # Kontrollera var 5:e sekund
        new_referral_bonus = get_referral_bonus(email)

        if new_referral_bonus != last_referral_bonus:
            last_referral_bonus = new_referral_bonus
            yield f"data: {json.dumps({'referral_bonus': new_referral_bonus})}\n\n"
        else:
            yield "data: ping\n\n"  # Håll anslutningen vid liv

def get_referral_count(email):
    """ Hämtar referral count från MongoDB """
    user = users_collection.find_one({"email": email})
    return user.get("referrals", 0) if user else 0

def get_referral_bonus(email):
    """ Hämtar referral bonus från MongoDB """
    user = users_collection.find_one({"email": email})
    return user.get("referral_bonus", 0) if user else 0


