from flask import Blueprint, request, jsonify, url_for, render_template
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from datetime import datetime
import uuid
from database.mongo_connection import collection

"""
User Registration Module

This module handles user registration, including:
- Serving the registration page (GET request)
- Handling user registration (POST request)
- Validating user input
- Storing user credentials securely
"""

# Define Blueprint for registration routes
register_bp = Blueprint("register_bp", __name__)

# Load environment variables
load_dotenv()


# User Registration Route
@register_bp.route("/register", methods=["GET", "POST"])
def register():

    """Handles user registration and serves the registration form."""
    if request.method == "GET":

        return render_template("register/register.html")

    print("Received a POST request at /register")

    if request.content_type != "application/json":

        print("Invalid Content-Type:", request.content_type)
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415
    

    try:

        # Parse JSON request data
        data = request.get_json()
        print("Received Data:", data)

        # Validate required fields
        if "email" not in data or "password" not in data:

            print("Missing email or password")

            return jsonify({"error": "Missing email or password"}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        hashed_password = generate_password_hash(password)

        print("Checking if user already exists...")
        existing_users = list(collection.find({"email": email}))

        if existing_users:

            print("Email already registered:", email)
            return jsonify({"error": "Email already registered."}), 409

        # Create user document
        user_document = {

            "_id": str(uuid.uuid4()),
            "email": email,
            "passwordHash": hashed_password,
            "createdAt": datetime.utcnow().isoformat(),

        }

        print("Inserting user into database:", user_document)
        collection.insert_one(user_document)

        print("Registration successful!")
        return jsonify({"message": "Registration successful!", "redirect_url": url_for("signin_bp.signin", _external=True)}), 201

    except Exception as e:

        print(f"ERROR: {e}")  # 🔥 Log the error
        return jsonify({"error": f"Database error: {str(e)}"}), 500
