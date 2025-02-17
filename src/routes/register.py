from flask import Blueprint, request, jsonify, url_for, render_template
from azure.cosmos import exceptions
import uuid
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from datetime import datetime
from database.mongo_connection import collection

# ✅ Define Blueprint
register_bp = Blueprint("register_bp", __name__)

# Load environment variables
load_dotenv()


@register_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register/register.html")

    if request.content_type == "application/json":
        data = request.get_json()
    else:
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    if "email" not in data or "password" not in data:
        return jsonify({"error": "Missing email or password"}), 400

    email = data["email"].lower().strip()
    password = data["password"]
    hashed_password = generate_password_hash(password)

    query = {"email": email}
    existing_user = collection.find_one(query)

    if existing_user:
        return jsonify({"error": "Email already registered."}), 409

    user_document = {
        "_id": str(uuid.uuid4()),
        "email": email,
        "passwordHash": hashed_password,
        "createdAt": datetime.utcnow().isoformat(),
    }

    try:
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
