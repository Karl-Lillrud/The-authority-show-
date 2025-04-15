from flask import Blueprint, request, jsonify, redirect, render_template, flash, url_for, session, current_app
from backend.repository.auth_repository import AuthRepository
from backend.services.TeamInviteService import TeamInviteService
from backend.services.authService import AuthService
import os
import logging  # Add logging import
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from backend.database.mongo_connection import collection
from datetime import datetime  
from bson import ObjectId  # Add this import for ObjectId
import uuid  # Add this import for generating unique IDs

# Define Blueprint
auth_bp = Blueprint("auth_bp", __name__)

# Instantiate the Auth Repository
auth_repo = AuthRepository()

auth_service = AuthService()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Instantiate AuthService

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


@auth_bp.route("/signin", methods=["GET"], endpoint="signin_page")
@auth_bp.route("/", methods=["GET"], endpoint="root_signin_page")
def signin_page():
    """
    Serves the sign-in page.
    """
    # Check if the user has an active session cookie
    if "user_id" in session and session.get("user_id"):
        return redirect("/dashboard")  # Redirect to dashboard if session is active

    if request.cookies.get("remember_me") == "true":
        return redirect("/podprofile")  # Redirect to podprofile instead of dashboard
    return render_template("signin/signin.html", API_BASE_URL=API_BASE_URL)


@auth_bp.route("/signin", methods=["POST"], endpoint="signin_submit")
def signin_submit():
    """
    Handle OTP-based sign-in.
    """
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")

    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400

    response, status_code = auth_service.verify_otp_and_login(email, otp)

    if status_code == 200 and response.get("user_authenticated"):
        user = response.get("user")
        session["user_id"] = str(user["_id"])
        session["email"] = user["email"]
        logger.info(f"User {user['email']} logged in successfully.")
        return jsonify({"redirect_url": "/dashboard"}), 200
    else:
        logger.warning("Failed OTP login attempt.")
        return jsonify({"error": response.get("error", "Invalid OTP")}), 401


@auth_bp.route("/logout", methods=["GET"])
def logout_user():
    """
    Logs out the user by clearing the session.
    """
    session.clear()  # Clear all session data
    return jsonify({"message": "Logout successful", "redirect_url": "/signin"}), 200


@auth_bp.route("/verify-and-signin", methods=["POST"], endpoint="verify_and_signin")
def verify_and_signin():
    """
    Endpoint to verify the code and sign in the user.
    """
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    email = data.get("email")
    code = data.get("code")

    if not email or not code:
        return jsonify({"error": "Email and code are required"}), 400

    try:
        # Call the AuthService to verify the code
        result = auth_service.verify_code_and_login(email, code)

        if result.get("status") == 200:
            user = collection.find_one({"email": email})
            if not user:
                # Create a new user if not existing
                user_data = {
                    "id": str(uuid.uuid4()),  # Generate a unique UUID for the user ID
                    "email": email,
                    "created_at": datetime.utcnow(),
                }
                collection.insert_one(user_data)
                user = collection.find_one({"id": user_data["id"]})

                # Create an account for the user
                account_data = {
                    "id": str(uuid.uuid4()),  # Generate a unique UUID for the account ID
                    "userId": user["id"],
                    "email": email,
                    "created_at": datetime.utcnow(),
                    "isActive": True,
                }
                collection.database.Accounts.insert_one(account_data)

            # Log the user in by setting session variables
            session["user_id"] = user["id"]
            session["email"] = user["email"]

            return jsonify(result), 200
        elif result.get("status") == 400:
            logger.warning(f"Invalid or expired code for email: {email}")
            return jsonify({"error": "Invalid or expired code"}), 400
        else:
            logger.error(f"Unexpected error during code verification: {result}")
            return jsonify({"error": "An unexpected error occurred"}), 500
    except Exception as e:
        logger.error(f"Error verifying code for email {email}: {e}", exc_info=True)
        return jsonify({"error": f"Failed to verify code: {str(e)}"}), 500


@auth_bp.route("/send-login-link", methods=["POST"], endpoint="send_login_link")
def send_login_link():
    """
    Endpoint to send a log-in link to the user's email.
    """
    if request.content_type != "application/json":
        logger.error("Invalid Content-Type. Expected application/json")
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    email = data.get("email")

    if not email:
        logger.error("Email is required but not provided")
        return jsonify({"error": "Email is required"}), 400

    try:
        # Generate a secure token
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        token = serializer.dumps(email, salt="login-link-salt")

        # Construct the log-in link
        login_link = f"{request.host_url}signin?token={token}"
        logger.info(f"Generated log-in link for {email}: {login_link}")

        # Send the log-in link via email
        auth_service.send_login_email(email, login_link)

        logger.info(f"Log-in link sent successfully to {email}")
        return jsonify({"message": "Log-in link sent successfully"}), 200
    except Exception as e:
        logger.error(f"Error sending log-in link for {email}: {e}", exc_info=True)
        return jsonify({"error": "Failed to send log-in link. Please try again later."}), 500


@auth_bp.route("/verify-login-token", methods=["POST"], endpoint="verify_login_token")
def verify_login_token():
    """
    Endpoint to verify the login token and log the user in.
    """
    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"error": "Token is required"}), 400

    try:
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        email = serializer.loads(token, salt="login-link-salt", max_age=600)  # Token valid for 10 minutes

        # Check if the user exists in the database
        user = collection.find_one({"email": email})
        if not user:
            # Create a new user if not existing
            user_data = {
                "id": str(uuid.uuid4()),  # Generate a unique UUID for the user ID
                "email": email,
                "createdAt": datetime.utcnow(),
            }
            collection.insert_one(user_data)
            user = collection.find_one({"id": user_data["id"]})

        # Log the user in by setting session variables
        session["user_id"] = user["id"]
        session["email"] = user["email"]

        return jsonify({"redirect_url": "/podprofile"}), 200  # Redirect to /podprofile
    except SignatureExpired:
        logger.error("Token has expired")
        return jsonify({"error": "Token has expired"}), 400
    except BadSignature:
        logger.error("Invalid token signature")
        return jsonify({"error": "Invalid token"}), 400
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# Ensure account creation logic is properly integrated
@auth_bp.route("/signin", methods=["POST"], endpoint="signin")
def signin():
    """
    Handles user sign-in.
    """
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        # Authenticate user
        user = auth_service.authenticate_user(email, password)
        if user:
            session["user_id"] = str(user["_id"])  # Set user_id in session
            session["email"] = user["email"]
            
            # Ensure account exists for the user
            account = collection.database.Accounts.find_one({"userId": str(user["_id"])})
            if not account:
                account_data = {
                    "id": str(uuid.uuid4()),
                    "userId": str(user["_id"]),
                    "email": email,
                    "created_at": datetime.utcnow(),
                    "isActive": True,
                }
                collection.database.Accounts.insert_one(account_data)

            return jsonify({"redirect_url": "/podprofile"}), 200  # Redirect to /podprofile
        else:
            # If user is not found, create a new account
            user_id = str(uuid.uuid4())
            user_data = {
                "_id": user_id,
                "email": email,
                "password": auth_service.hash_password(password),  # Hash the password
                "createdAt": datetime.utcnow().isoformat(),
            }
            collection.insert_one(user_data)

            # Create an account for the user
            account_data = {
                "id": str(uuid.uuid4()),
                "userId": user_id,
                "email": email,
                "created_at": datetime.utcnow(),
                "isActive": True,
            }
            collection.database.Accounts.insert_one(account_data)

            # Log the user in by setting session variables
            session["user_id"] = user_id
            session["email"] = email

            return jsonify({"redirect_url": "/podprofile"}), 200
    except Exception as e:
        logger.error(f"Error during sign-in: {e}", exc_info=True)
        return jsonify({"error": "An error occurred during sign-in"}), 500
