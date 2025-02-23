from flask import Blueprint, request, jsonify, url_for, render_template
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from datetime import datetime
import uuid
from database.mongo_connection import collection

# Define Blueprint
register_bp = Blueprint("register_bp", __name__)

# Load environment variables
load_dotenv()

@register_bp.route("/register", methods=["GET", "POST"])
def register():
    email = request.args.get('email', '')
    if request.method == "GET":
        return render_template("register/register.html", email=email)

    if request.content_type != "application/json":
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

        existing_users = list(collection.find({"email": email}))

        if existing_users:
            return jsonify({"error": "Email already registered."}), 409

        user_document = {
            "_id": str(uuid.uuid4()),
            "email": email,
            "passwordHash": hashed_password,
            "createdAt": datetime.utcnow().isoformat(),
        }

        collection.insert_one(user_document)

        return (
            jsonify(
                {
                    "message": "Registration successful!",
                    "redirect_url": url_for("signin_bp.signin", _external=True),
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
