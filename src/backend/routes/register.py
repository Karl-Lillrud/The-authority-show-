from flask import Blueprint, request, jsonify, url_for, render_template, g
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from datetime import datetime
import uuid
import re
from backend.database.mongo_connection import collection
from backend.services.accountsService import create_account  # Correct the import path
from backend.utils.email_utils import check_gmail_existence  # Function to verify Gmail existence

register_bp = Blueprint("register_bp", __name__)

load_dotenv()

@register_bp.route("/register", methods=["GET"])
def register_get():
    return render_template("register/register.html")

@register_bp.route("/register", methods=["POST"])
def register_post():
    print("🔍 Received a POST request at /register")

    if request.content_type != "application/json":
        print("❌ Invalid Content-Type:", request.content_type)
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    try:
        data = request.get_json()
        print("📩 Received Data:", data)

        if "email" not in data or "password" not in data:
            print("❌ Missing email or password")
            return jsonify({"error": "Missing email or password"}), 400

        email = data["email"].lower().strip()
        password = data["password"]

        # Validate password: at least 8 characters and must contain at least one letter and one number.
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long."}), 400
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            return jsonify({"error": "Password must contain at least one letter and one number."}), 400

        # If it's a Gmail address, verify that it exists.
        if email.endswith("@gmail.com") and not check_gmail_existence(email):
            return jsonify({"error": "Provided Gmail address does not exist."}), 400

        hashed_password = generate_password_hash(password)

        print("🔍 Checking if user already exists...")
        existing_users = list(collection.database.Users.find({"email": email}))

        if existing_users:
            print("⚠️ Email already registered:", email)
            return jsonify({"error": "Email already registered."}), 409

        # ✅ Generate unique user ID (string UUID)
        user_id = str(uuid.uuid4())

        # Create the User document (set '_id' as the string UUID)
        user_document = {
            "_id": user_id,
            "email": email,
            "passwordHash": hashed_password,
            "createdAt": datetime.utcnow().isoformat(),
        }

        print("📝 Inserting user into database:", user_document)
        collection.database.Users.insert_one(user_document)

        account_data = {
            "userId": user_id,
            "email": email,
            "companyName": data.get("companyName", ""),
            "isCompany": data.get("isCompany", False),
            "ownerId": user_id,
        }

        account_response, status_code = create_account(account_data)

        if status_code != 201:
            return jsonify({"error": "Failed to create account", "details": account_response}), 500

        account_id = account_response["accountId"]

        print("✅ Registration successful!")
        return jsonify({
            "message": "Registration successful!",
            "userId": user_id,
            "accountId": account_id,
            "redirect_url": url_for("signin_bp.signin_get", _external=True)
        }), 201

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@register_bp.route("/get_email", methods=["GET"])
def get_email():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = str(g.user_id)
        user = collection.database.Users.find_one({"_id": user_id}, {"email": 1, "_id": 0})

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"email": user["email"]}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch email: {str(e)}"}), 500
