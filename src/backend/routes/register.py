from flask import Blueprint, request, jsonify, url_for, render_template
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from datetime import datetime
import uuid
import requests
from backend.database.mongo_connection import collection
from backend.services.account_service import (
    create_account,
)  # Import the account creation function
import os
import logging

register_bp = Blueprint("register_bp", __name__)

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@register_bp.route("/register", methods=["GET", "POST"])
def register():
    email = request.args.get("email", "")
    if request.method == "GET":
        return render_template("register/register.html", email=email)

    if request.content_type != "application/json":
        logger.error("Invalid Content-Type: %s", request.content_type)
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    try:
        data = request.get_json()

        if "email" not in data or "password" not in data:
            return jsonify({"error": "Missing email or password"}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        hashed_password = generate_password_hash(password)

        logger.info("Checking if user already exists...")
        existing_users = list(collection.database.Users.find({"email": email}))

        if existing_users:
            return jsonify({"error": "Email already registered."}), 409

        # Generate unique user ID (string UUID)
        user_id = str(uuid.uuid4())

        # Create the User document (set '_id' as the string UUID)
        user_document = {
            "_id": user_id,  # Explicitly set '_id' to string UUID
            "email": email,
            "passwordHash": hashed_password,  # Hashed for security
            "createdAt": datetime.utcnow().isoformat(),
        }

        # Insert user into the Users collection with the correct '_id'
        logger.info("Inserting user into database: %s", user_document)
        collection.database.Users.insert_one(user_document)

        account_data = {
            "userId": user_id,  # Use string user ID
            "email": email,
            "companyName": data.get("companyName", ""),
            "isCompany": data.get("isCompany", False),
        }

        # Call the account creation function directly
        account_response = create_account(account_data)

        # Check if account creation was successful
        if not account_response["success"]:
            logger.error("Error response content: %s", account_response["details"])
            return (
                jsonify(
                    {
                        "error": "Failed to create account",
                        "details": account_response["details"],
                    }
                ),
                500,
            )

        # Get the account ID from the response of the account creation
        account_id = account_response["accountId"]

        logger.info("Registration successful!")
        return (
            jsonify(
                {
                    "message": "Registration successful!",
                    "userId": user_id,
                    "accountId": account_id,
                    "redirect_url": url_for("signin_bp.signin", _external=True),
                }
            ),
            201,
        )

    except Exception as e:
        logger.error("Error: %s", e, exc_info=True)
        return jsonify({"error": f"Database error: {str(e)}"}), 500
