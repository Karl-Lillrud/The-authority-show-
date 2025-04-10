from flask import Blueprint, request, jsonify, redirect, render_template, flash, url_for, session
from backend.repository.auth_repository import AuthRepository
from backend.services.TeamInviteService import TeamInviteService
from backend.services.authService import AuthService
import os
import logging  # Add logging import

# Define Blueprint
auth_bp = Blueprint("auth_bp", __name__)

# Instantiate the Auth Repository
auth_repo = AuthRepository()

auth_service = AuthService()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Instantiate AuthService
@auth_bp.route("/send-verification-code", methods=["POST"])
def send_verification_code():
    """
    Endpoint to send a verification code to the user's email
    """
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    try:
        # Call the AuthService to send the verification code
        result = auth_service.send_verification_code(email)
        if result.get("error"):
            return jsonify(result), 400
        return jsonify({"message": "Verification code sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to send verification code: {str(e)}"}), 500

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


@auth_bp.route("/signin", methods=["GET"], endpoint="signin")
@auth_bp.route("/", methods=["GET"])
def signin_page():
    if request.cookies.get("remember_me") == "true":
        return redirect("/dashboard")
    return render_template("signin/signin.html", API_BASE_URL=API_BASE_URL)


@auth_bp.route("/signin", methods=["POST"])
@auth_bp.route("/", methods=["POST"])
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
    response = auth_repo.logout()
    # Ensure the response is JSON-serializable
    if isinstance(response, dict):
        return jsonify(response), 200
    return jsonify({"message": "Logout successful"}), 200


@auth_bp.route("/register", methods=["GET"])
def register_page():
    # Get the invite token from the URL parameters
    invite_token = request.args.get("token")

    if invite_token:
        # Verify the invite token
        invite_service = TeamInviteService()
        response, status = invite_service.verify_invite(invite_token)

        if status == 200:
            # Render the team member registration form with the invite data
            return render_template(
                "team/register-team-member.html",
                email=response.get("email"),
                team_name=response.get("teamName", "the team"),
                invite_token=invite_token,
            )
        else:
            flash(response.get("error", "Invalid invitation link"), "error")
            return redirect(url_for("auth_bp.signin"))

    # Regular registration page if no token
    return render_template("register/register.html")


@auth_bp.route("/register", methods=["POST"])
def register_submit():
    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    data = request.get_json()
    response, status_code = auth_repo.register(data)
    # Convert possible Response object into a JSON dict
    if hasattr(response, "get_json"):
        response = response.get_json()
    return jsonify(response), status_code


@auth_bp.route("/register-team-member", methods=["GET"])
def register_team_member_page():
    return render_template("register/register_team_member.html")


@auth_bp.route("/register-team-member", methods=["POST"])
def register_team_member_submit():
    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    data = request.get_json()
    response, status_code = auth_repo.register_team_member(data)
    # Convert possible Response object into a JSON dict
    if hasattr(response, "get_json"):
        response = response.get_json()

    if status_code == 201:
        invite_token = data.get("inviteToken")
        if invite_token:
            invite_service = TeamInviteService()
            invite_response, invite_status = invite_service.process_registration(
                user_id=response.get("userId"),
                email=data.get("email"),
                invite_token=invite_token,
            )
            if invite_status == 201:
                response["teamId"] = invite_response.get("teamId")
                response["teamMessage"] = invite_response.get("message")
    return jsonify(response), status_code


@auth_bp.route("/verify-and-signin", methods=["POST"])
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
        # Call the AuthService to verify the code and log in the user
        result = auth_service.verify_code_and_login(email, code)
        return jsonify(result), result.get("status", 200)
    except Exception as e:
        return jsonify({"error": f"Failed to verify code: {str(e)}"}), 500


@auth_bp.route("/send-login-link", methods=["POST"])
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
        # Construct the log-in link
        login_link = f"{request.host_url}podprofile?email={email}"
        logger.info(f"Generated log-in link for {email}: {login_link}")

        # Send the log-in link via email
        auth_service.send_login_email(email, login_link)

        logger.info(f"Log-in link sent successfully to {email}")
        return jsonify({"message": "Log-in link sent successfully"}), 200
    except Exception as e:
        logger.error(f"Error sending log-in link for {email}: {e}", exc_info=True)
        return jsonify({"error": "Failed to send log-in link. Please try again later."}), 500
