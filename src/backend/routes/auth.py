from flask import Blueprint, request, jsonify, redirect, render_template, session
from backend.services.authService import AuthService
from backend.utils.email_utils import send_login_email
import logging
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app

auth_bp = Blueprint("auth_bp", __name__)
auth_service = AuthService()
logger = logging.getLogger(__name__)


@auth_bp.route("/signin", methods=["GET"], endpoint="signin_page")
@auth_bp.route("/", methods=["GET"], endpoint="root_signin_page")
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
        logger.error("Email saknas i begäran")
        return jsonify({"error": "Email krävs"}), 400

    try:
        # Kontrollera att SECRET_KEY är konfigurerad
        if not current_app.config.get("SECRET_KEY"):
            logger.error("SECRET_KEY är inte konfigurerad")
            return jsonify({"error": "Serverkonfigurationsfel: SECRET_KEY saknas"}), 500

        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        token = serializer.dumps(email, salt="login-link-salt")
        login_link = f"{request.host_url}signin?token={token}"
        result = send_login_email(email, login_link)
        if result.get("success"):
            return jsonify({"message": "Inloggningslänk skickad"}), 200
        else:
            logger.error(
                f"Misslyckades att skicka inloggningslänk till {email}: {result.get('error')}"
            )
            return (
                jsonify(
                    {
                        "error": f"Misslyckades att skicka inloggningslänk: {result.get('error')}"
                    }
                ),
                500,
            )
    except Exception as e:
        logger.error(
            f"Fel vid sändning av inloggningslänk för {email}: {str(e)}", exc_info=True
        )
        return jsonify({"error": f"Internt serverfel: {str(e)}"}), 500


@auth_bp.route("/verify-login-token", methods=["POST"], endpoint="verify_login_token")
def verify_login_token():
    data = request.get_json()
    token = data.get("token")
    if not token:
        logger.error("Token saknas i begäran")
        return jsonify({"error": "Token krävs"}), 400

    try:
        response, status_code = auth_service.verify_login_token(token)
        return jsonify(response), status_code
    except SignatureExpired:
        logger.error("Token har gått ut")
        return jsonify({"error": "Token har gått ut"}), 400
    except BadSignature:
        logger.error("Ogiltig token")
        return jsonify({"error": "Ogiltig token"}), 400
    except Exception as e:
        logger.error(f"Fel vid verifiering av token: {e}", exc_info=True)
        return jsonify({"error": f"Internt serverfel: {str(e)}"}), 500


@auth_bp.route("/verify-otp", methods=["POST"], endpoint="verify_otp")
def verify_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")
    if not email or not otp:
        logger.error("Email eller OTP saknas i begäran")
        return jsonify({"error": "Email och OTP krävs"}), 400

    try:
        response, status_code = auth_service.verify_otp_and_login(email, otp)
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"Fel vid OTP-verifiering: {e}", exc_info=True)
        return jsonify({"error": f"Internt serverfel: {str(e)}"}), 500


@auth_bp.route("/logout", methods=["GET"])
def logout_user():
    session.clear()
    response = jsonify(
        {"message": "Utloggning framgångsrik", "redirect_url": "/signin"}
    )
    response.delete_cookie("remember_me")
    return response, 200
