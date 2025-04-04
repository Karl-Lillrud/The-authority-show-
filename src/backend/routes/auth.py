from flask import Blueprint, request, jsonify, redirect, render_template, flash, url_for
from backend.repository.auth_repository import AuthRepository
from backend.services.TeamInviteService import TeamInviteService
from backend.services.authService import AuthService
import os

# Define Blueprint
auth_bp = Blueprint("auth_bp", __name__)

# Instantiate the Auth Repository
auth_repo = AuthRepository()

auth_service = AuthService()

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
    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    data = request.get_json()
    response, status_code = auth_repo.signin(data)
    return jsonify(response), status_code


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
