from flask import (
    render_template,
    request,
    jsonify,
    session,
    Blueprint,
    redirect,
    url_for,
    g,
)
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database.mongo_connection import collection
from backend.services.authService import validate_password, validate_email
import os
import uuid
from datetime import datetime

from backend.services.accountsService import create_account

auth_bp = Blueprint("auth_bp", __name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

#USE FOR AUTHENTICATION SECURITY PURPOSES REGISTER, SIGNIN, LOGOUT/ users collection
#USER.PY Can be used for user specific data
#ACCOUNT.PY Can be used for account specific data

@auth_bp.route("/signin", methods=["GET"], endpoint="signin")
@auth_bp.route("/", methods=["GET"])
def signin_page():
    if request.cookies.get("remember_me") == "true":
        return redirect("/dashboard")
    return render_template("signin.html", API_BASE_URL=API_BASE_URL)


@auth_bp.route("/signin", methods=["POST"])
@auth_bp.route("/", methods=["POST"])
def signin_submit():
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    remember = data.get("remember", False)

    user = collection.find_one({"email": email})

    if not user or not check_password_hash(user["passwordHash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = str(user["_id"])
    session["email"] = user["email"]
    session.permanent = remember

    user_id = session["user_id"]
    podcasts = list(collection.database.Podcast.find({"userid": user_id}))

    redirect_url = (
        "/podprofile" if not podcasts else "/dashboard" if len(podcasts) == 1 else "/homepage"
    )

    response = jsonify({"message": "Login successful", "redirect_url": redirect_url})
    
    if remember:
        response.set_cookie("remember_me", "true", max_age=30 * 24 * 60 * 60)  # 30 days
    else:
        response.delete_cookie("remember_me")

    return response, 200


@auth_bp.route("/logout", methods=["GET"])
def logout_user():
    session.clear()
    response = redirect(url_for("auth_bp.signin"))
    response.delete_cookie("remember_me")
    return response


@auth_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("register/register.html")


@auth_bp.route("/register", methods=["POST"])
def register_submit():
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

        # Validate email using the function from authService
        email_error = validate_email(email)
        if email_error:
            return email_error  # If there's an error with the email validation, return it.

        # Validate password using the function from authService
        password_error = validate_password(password)
        if password_error:
            return password_error  # If there's an error with the password validation, return it.

        hashed_password = generate_password_hash(password)

        print("🔍 Checking if user already exists...")
        if collection.database.Users.find_one({"email": email}):
            print("⚠️ Email already registered:", email)
            return jsonify({"error": "Email already registered."}), 409

        user_id = str(uuid.uuid4())
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
            "redirect_url": url_for("auth_bp.signin", _external=True),
        }), 201

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500