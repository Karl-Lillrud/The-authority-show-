from flask import render_template, request, jsonify, url_for, Blueprint
import os
import random
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash
from database.mongo_connection import collection

"""
Forgot Password Module

This module provides routes for handling password reset functionality.
It includes:
- Requesting a password reset (sending a reset code via email).
- Verifying the reset code.
- Resetting the password.
- Resending the reset code if needed.
"""

# Define Flask Blueprint for forgot password operations
forgotpass_bp = Blueprint("forgotpass_bp", __name__)

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


# Request Password Reset
@forgotpass_bp.route("/forgotpassword", methods=["GET", "POST"])
def forgot_password():

    if request.method == "GET":
        
        return render_template("forgotpassword/forgot-password.html")

    if request.content_type != "application/json":

        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    if not data:

        return jsonify({"error": "Invalid JSON format"}), 400

    email = data.get("email", "").strip().lower()
    print(f"🔍 Checking for email: {email}")
    
    users = list(collection.find({"email": email}))
    if not users:

        return jsonify({"error": "No account found with that email"}), 404

    # Generate and store reset code
    reset_code = str(random.randint(100000, 999999))
    collection.update_one({"_id": users[0]["_id"]}, {"$set": {"reset_code": reset_code}})

    try:

        send_reset_email(email, reset_code)
        return jsonify({"message": "Reset code sent successfully.", "redirect_url": url_for("forgotpass_bp.enter_code")}), 200
    
    except Exception as e:

        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500


# Enter Reset Code
@forgotpass_bp.route("/enter-code", methods=["GET", "POST"])
def enter_code():

    if request.method == "GET":

        return render_template("forgotpassword/enter-code.html")

    if request.content_type != "application/json":

        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:

        data = request.get_json(force=True)

    except Exception:

        return jsonify({"error": "Invalid JSON format"}), 400

    email = data.get("email", "").strip().lower()
    entered_code = data.get("code", "").strip()
    users = list(collection.find({"email": email}))

    if not users or users[0].get("reset_code") != entered_code:

        return jsonify({"error": "Invalid or expired reset code."}), 400

    return jsonify({"message": "Code is Valid.", "redirect_url": url_for("forgotpass_bp.reset_password")}), 200


# Reset Password
@forgotpass_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if request.method == "GET":
        return render_template("forgotpassword/reset-password.html")

    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    email = data.get("email", "").strip().lower()
    new_password = data.get("password", "")

    users = list(collection.find({"email": email}))

    if not users:
        return jsonify({"error": "User not found."}), 404

    user = users[0]
    user["passwordHash"] = generate_password_hash(new_password)
    collection.update_one({"_id": user["_id"]}, {"$set": user})

    return jsonify({"message": "Password updated successfully.", "redirect_url": url_for("signin")}), 200


# Send Reset Email
def send_reset_email(email, reset_code):
    try:

        msg = MIMEText(f"Your password reset code is: {reset_code}\nUse this code to reset your password.")
        msg["Subject"] = "Password Reset Request"
        msg["From"] = EMAIL_USER if EMAIL_USER else "no-reply@example.com"
        msg["To"] = email

        if not SMTP_SERVER or not SMTP_PORT:

            raise ValueError("SMTP_SERVER and SMTP_PORT must be set")
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:

            server.starttls()
            if EMAIL_USER and EMAIL_PASS:
                server.login(EMAIL_USER, EMAIL_PASS)

            else:
                raise ValueError("EMAIL_USER and EMAIL_PASS must be set")
            
            server.sendmail(EMAIL_USER, email, msg.as_string())

    except Exception as e:

        print(f"Error sending email: {e}")

        raise


# Resend Code
@forgotpass_bp.route("/resend-code", methods=["POST"])
def resend_code():

    if request.content_type != "application/json":

        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    email = data.get("email", "").strip().lower()
    users = list(collection.find({"email": email}))

    if not users:

        return jsonify({"error": "No account found with that email"}), 404

    reset_code = str(random.randint(100000, 999999))
    collection.update_one({"_id": users[0]["_id"]}, {"$set": {"reset_code": reset_code}})

    try:

        send_reset_email(email, reset_code)
        return jsonify({"message": "New reset code sent successfully."}), 200
    
    except Exception as e:

        return jsonify({"error": f"Failed to resend code: {str(e)}"}), 500
