from flask import Blueprint, jsonify, request, Response, stream_with_context
from backend.database.mongo_connection import collection
import smtplib
import os
import ssl
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

credits_bp = Blueprint('credits_bp', __name__)

def get_user_by_email(email):
    user = collection.database.Users.find_one({"email": email.lower().strip()})
    logger.debug(f"get_user_by_email: Found user: {user}")
    return user

@credits_bp.route('/credits', methods=['GET'])
def get_credits():
    email = request.args.get("email")
    logger.debug(f"/credits endpoint called with email: {email}")
    if not email:
        logger.error("Email parameter is missing")
        return jsonify({"error": "Email is required"}), 400
    user = get_user_by_email(email)
    if not user:
        logger.error("User not found")
        return jsonify({"error": "User not found"}), 404
    credits = collection.database.Credits.find_one({"user_id": user["_id"]})
    if not credits:
        logger.error("Credits document not found")
        return jsonify({"error": "No credits found"}), 404
    logger.debug(f"Credits for user {user['_id']}: {credits}")
    return jsonify({
        "user_id": user["_id"],
        "credits": credits.get("credits", 0),
        "credits_expires_at": credits.get("credits_expires_at", "N/A")
    })

@credits_bp.route('/user-progress', methods=['GET'])
def user_progress():
    email = request.args.get("email")
    logger.debug(f"/user-progress endpoint called with email: {email}")
    if not email:
        logger.error("Email parameter is missing")
        return jsonify({"error": "Email is required"}), 400
    user = get_user_by_email(email)
    if not user:
        logger.error("User not found")
        return jsonify({"error": "User not found"}), 404
    credits = collection.database.Credits.find_one({"user_id": user["_id"]})
    if not credits:
        logger.error("Credits document not found")
        return jsonify({"error": "No credits found"}), 404
    return jsonify({
        "user_id": user["_id"],
        "credits": credits.get("credits", 0),
        "unclaimed_credits": credits.get("unclaimed_credits", 0),
        "referral_bonus": credits.get("referral_bonus", 0),
        "referrals": credits.get("referrals", 0),
        "episodes_published": credits.get("episodes_published", 0),
        "streak_days": credits.get("streak_days", 0)
    })

@credits_bp.route("/claim-reward", methods=["POST"])
def claim_reward():
    data = request.json
    logger.debug(f"/claim-reward data: {data}")
    email = data.get("email")
    if not email:
        logger.error("Email is missing in claim-reward")
        return jsonify({"error": "Email is required"}), 400
    user = get_user_by_email(email)
    if not user:
        logger.error("User not found in claim-reward")
        return jsonify({"error": "User not found"}), 404
    user_id = user["_id"]
    credits = collection.database.Credits.find_one({"user_id": user["_id"]})
    if not credits:
        logger.error("Credits document not found in claim-reward")
        return jsonify({"error": "No credits found"}), 404
    total_claimable = credits.get("unclaimed_credits", 0) + credits.get("referral_bonus", 0)
    logger.debug(f"Total claimable credits: {total_claimable}")
    if total_claimable == 0:
        logger.error("No credits available to claim")
        return jsonify({"error": "No credits available to claim"}), 400
    update_result = collection.database.Credits.update_one(
        {"user_id": user_id},
        {"$inc": {"credits": total_claimable},
         "$set": {"unclaimed_credits": 0, "referral_bonus": 0}}
    )
    logger.debug(f"Claim reward update result: {update_result.raw_result}")
    return jsonify({"success": True, "message": f"{total_claimable} credits claimed!"}), 200

@credits_bp.route("/send-invite", methods=["POST"])
def send_invite():
    data = request.json
    logger.debug(f"/send-invite data: {data}")
    friend_email = data.get("email")
    referral_code = data.get("referralCode")
    if not friend_email or not referral_code:
        logger.error("Missing email or referral code in send-invite")
        return jsonify({"error": "Missing email or referral code"}), 400
    referrer = collection.find_one({"referral_code": referral_code})
    if not referrer:
        logger.error("Invalid referral code provided in send-invite")
        return jsonify({"error": "Invalid referral code"}), 404
    sender_email = referrer["email"]
    subject = f"🎉 {sender_email} has invited you to PodManager!"
    message = f"""
    <h2>🚀 {sender_email} has invited you to PodManager!</h2>
    <p>Join now and get <b>3,000 free credits</b> to kickstart your podcast!</p>
    <a href="http://127.0.0.1:8000/register?referral={referral_code}">
        Register Now
    </a>
    """
    logger.debug(f"Attempting to send invite email to {friend_email}")
    if send_email(friend_email, subject, message):
        logger.info(f"Invite email sent successfully to {friend_email}")
        return jsonify({"message": "Invite sent!"}), 200
    else:
        logger.error("Failed to send invite email")
        return jsonify({"error": "Failed to send invite"}), 500

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
        logger.debug("Email sent successfully")
        return True
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return False

@credits_bp.route("/get-referral-status", methods=["GET"])
def get_referral_status():
    email = request.args.get("email")
    logger.debug(f"/get-referral-status called with email: {email}")
    if not email:
        logger.error("Email parameter is missing in get-referral-status")
        return jsonify({"error": "Email is required"}), 400
    user = get_user_by_email(email)
    if not user:
        logger.error("User not found in get-referral-status")
        return jsonify({"error": "User not found"}), 404
    credits = collection.database.Credits.find_one({"user_id": user["_id"]})
    if not credits:
        logger.error("Credits document not found in get-referral-status")
        return jsonify({"error": "No credits found"}), 404
    return jsonify({
        "referrals": credits.get("referrals", 0),
        "redirect": credits.get("referrals", 0) > 0
    })

@credits_bp.route("/stream-referral-updates", methods=["GET"])
def stream_referral_updates():
    email = request.args.get("email")
    logger.debug(f"/stream-referral-updates called with email: {email}")
    if not email:
        logger.error("Email parameter is missing in stream-referral-updates")
        return jsonify({"error": "No email provided"}), 400
    return Response(stream_with_context(event_stream(email)), content_type="text/event-stream")

def event_stream(email):
    last_referral_bonus = get_referral_bonus(email)
    logger.debug(f"Starting event stream for {email} with initial bonus {last_referral_bonus}")
    while True:
        time.sleep(5)
        new_referral_bonus = get_referral_bonus(email)
        if new_referral_bonus != last_referral_bonus:
            last_referral_bonus = new_referral_bonus
            logger.debug(f"Referral bonus updated to {new_referral_bonus} for {email}")
            yield f"data: {json.dumps({'referral_bonus': new_referral_bonus, 'referrals': get_referral_count(email)})}\n\n"
        else:
            yield 'data: {"ping": true}\n\n'

def get_referral_count(email):
    user = get_user_by_email(email)
    if user:
        credits = collection.database.Credits.find_one({"user_id": user["_id"]})
        count = credits.get("referrals", 0) if credits else 0
        logger.debug(f"Referral count for {email} is {count}")
        return count
    return 0

def get_referral_bonus(email):
    user = get_user_by_email(email)
    if user:
        credits = collection.database.Credits.find_one({"user_id": user["_id"]})
        bonus = credits.get("referral_bonus", 0) if credits else 0
        logger.debug(f"Referral bonus for {email} is {bonus}")
        return bonus
    return 0
