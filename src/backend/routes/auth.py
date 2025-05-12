from flask import (
    Blueprint,
    request,
    jsonify,
    redirect,
    render_template,
    session,
    url_for,
    current_app,  # Ensure current_app is imported
)
from backend.services.authService import AuthService
from backend.utils.email_utils import send_login_email
import logging
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

auth_bp = Blueprint("auth_bp", __name__)
auth_service = AuthService()
logger = logging.getLogger(__name__)


@auth_bp.route("/signin", methods=["GET"], endpoint="signin_page")
def signin_page():
    if "user_id" in session and session.get("user_id"):
        return redirect("/dashboard")
    if request.cookies.get("remember_me") == "true":
        return redirect("/podprofile")
    return render_template("signin/signin.html")



@auth_bp.route("/signin", methods=["POST"], endpoint="signin")
def signin():
    data = request.get_json()
    response, status_code = auth_service.signin(data)
    if status_code == 200:
        response_obj = jsonify(response)
        response_obj.set_cookie("remember_me", "true", max_age=30 * 24 * 60 * 60)
        return response_obj, 200
    return jsonify(response), status_code


@auth_bp.route("/send-login-link", methods=["POST"], endpoint="send_login_link")
def send_login_link():
    data = request.get_json()
    email = data.get("email")
    if not email:
        logger.error("Email is missing in the request")
        return jsonify({"error": "Email is required"}), 400

    try:
        # --- Log SECRET_KEY used by web server ---
        WEB_SECRET_KEY = current_app.config.get("SECRET_KEY")
        if WEB_SECRET_KEY:
            logger.info(
                f"WEB_SERVER (/send-login-link): Using SECRET_KEY starting with: {WEB_SECRET_KEY[:5]}..."
            )
        else:
            logger.error(
                "WEB_SERVER (/send-login-link): SECRET_KEY is NOT configured in the Flask app!"
            )
            return (
                jsonify({"error": "Server configuration error: SECRET_KEY is missing"}),
                500,
            )
        # -----------------------------------------

        serializer = URLSafeTimedSerializer(WEB_SECRET_KEY)
        token = serializer.dumps(email, salt="login-link-salt")

        # --- Generate link using url_for ---
        # Use the endpoint name for the GET /signin route ('auth_bp.signin_page')
        try:
            login_link = url_for("auth_bp.signin_page", token=token, _external=True)
            logger.info(
                f"WEB_SERVER (/send-login-link): Generated login_link via url_for: {login_link}"
            )
        except Exception as url_err:
            logger.error(
                f"WEB_SERVER (/send-login-link): Failed to generate URL using url_for: {url_err}. Falling back to manual construction."
            )
            # Fallback (less ideal, but keeps functionality if url_for setup is tricky)
            login_link = f"{request.host_url}signin?token={token}"
            logger.info(
                f"WEB_SERVER (/send-login-link): Generated login_link manually (fallback): {login_link}"
            )
        # -----------------------------------

        result = send_login_email(email, login_link)
        if result.get("success"):
            return jsonify({"message": "Login link sent"}), 200
        else:
            logger.error(f"Failed to send login link to {email}: {result.get('error')}")
            return (
                jsonify({"error": f"Failed to send login link: {result.get('error')}"}),
                500,
            )
    except Exception as e:
        logger.error(f"Error sending login link for {email}: {str(e)}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@auth_bp.route("/verify-login-token", methods=["POST"], endpoint="verify_login_token")
def verify_login_token():
    # --- Log SECRET_KEY used by web server ---
    WEB_SECRET_KEY = current_app.config.get("SECRET_KEY")  # Get from app config
    if WEB_SECRET_KEY:
        logger.info(
            f"WEB_SERVER (/verify-login-token): Using SECRET_KEY from app.config starting with: {WEB_SECRET_KEY[:5]}..."
        )
    else:
        logger.error(
            "WEB_SERVER (/verify-login-token): SECRET_KEY is NOT configured in the Flask app!"
        )
        # Log error but let service handle potential failure
    # -----------------------------------------

    data = request.get_json()
    token = data.get("token")
    logger.info(
        f"WEB_SERVER (/verify-login-token): Received token in request body: {token}"
    )  # Keep this log
    try:
        response, status_code = auth_service.verify_login_token(token)
        return jsonify(response), status_code
    except SignatureExpired:
        logger.error("Token has expired")
        return jsonify({"error": "Token has expired"}), 400
    except BadSignature:
        logger.error("Invalid token")
        return jsonify({"error": "Invalid token"}), 400
    except Exception as e:
        logger.error(f"Error verifying token: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@auth_bp.route("/activate", methods=["GET"])
def activate_account_route():
    token = request.args.get("token")
    logger.info(f"Received activation request for token: {token}")
    if not token:
        logger.warn("Activation attempt with no token.")
        return jsonify({"error": "Activation token is missing."}), 400

    try:
        response_data, status_code = auth_service.process_activation_token(token)

        if status_code == 200:
            redirect_url = response_data.get("redirect_url", url_for("podprofile_bp.podprofile"))
            logger.info(f"Account activation processed. User ID: {session.get('user_id')}. Redirecting to {redirect_url}")
            return redirect(redirect_url)
        else:
            logger.error(f"Activation failed. Status: {status_code}, Response: {response_data}")
            return jsonify(response_data), status_code
    except Exception as e:
        logger.error(f"Exception during account activation: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred during activation."}), 500


@auth_bp.route("/verify-otp", methods=["POST"], endpoint="verify_otp")
def verify_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")
    if not email or not otp:
        logger.error("Email or OTP is missing in the request")
        return jsonify({"error": "Email and OTP are required"}), 400

    try:
        response, status_code = auth_service.verify_otp_and_login(email, otp)
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@auth_bp.route("/logout", methods=["GET"])
def logout_user():
    session.clear()
    response = jsonify({"message": "Logout successful", "redirect_url": "/signin"})
    response.delete_cookie("remember_me")
    return response, 200
