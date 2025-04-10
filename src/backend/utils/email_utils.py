import smtplib
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage  # Added for inline image support
from dotenv import load_dotenv
from flask import render_template, Blueprint, request, jsonify, url_for, redirect
import urllib.parse
import requests
from backend.repository.guest_repository import GuestRepository

# Load environment variables once
load_dotenv(override=True)

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")

# Configure logger
logger = logging.getLogger(__name__)

google_calendar_bp = Blueprint("google_calendar", __name__)
guest_repo = GuestRepository()

@google_calendar_bp.route("/save_google_refresh_token", methods=["POST"])
def save_google_refresh_token():
    """
    Save the Google OAuth2 refresh token in the Users collection.
    """
    try:
        data = request.json
        refresh_token = data.get("refreshToken")  # Ensure it's named refreshToken
        user_id = request.headers.get("User-ID")  # Assume User-ID is passed in headers

        if not refresh_token or not user_id:
            return jsonify({"error": "Missing refresh token or user ID"}), 400

        # Save the refresh token as googleRefresh
        result = collection.database.Users.update_one(
            {"_id": user_id},
            {"$set": {"googleRefresh": refresh_token}},  # Save as googleRefresh
            upsert=True
        )

        if result.modified_count > 0 or result.upserted_id:
            logger.info(f"✅ Refresh token saved successfully for user {user_id}.")
            return jsonify({"message": "Google refresh token saved successfully"}), 200
        else:
            logger.error(f"❌ Failed to save refresh token for user {user_id}.")
            return jsonify({"error": "Failed to save Google refresh token"}), 500
    except Exception as e:
        logger.exception("❌ ERROR: Failed to save Google refresh token")
        return jsonify({"error": f"Failed to save Google refresh token: {str(e)}"}), 500


@google_calendar_bp.route("/connect_google_calendar", methods=["GET"])
def connect_google_calendar():
    """
    Redirect the user to the Google OAuth URL for calendar access.
    """
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        scope = "https://www.googleapis.com/auth/calendar"
        response_type = "code"
        access_type = "offline"
        include_granted_scopes = "true"

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "response_type": response_type,
            "access_type": access_type,
            "include_granted_scopes": include_granted_scopes,
        }

        auth_url = f"{os.getenv('GOOGLE_OAUTH_URL')}?{urllib.parse.urlencode(params)}"
        return redirect(auth_url)  # Redirect the user to the Google OAuth page
    except Exception as e:
        logger.exception("❌ ERROR: Failed to generate Google OAuth URL")
        return jsonify({"error": f"Failed to generate Google OAuth URL: {str(e)}"}), 500


@google_calendar_bp.route("/calendar_callback", methods=["GET"])
def calendar_callback():
    """
    Handle the Google OAuth2 callback and exchange the authorization code for tokens.
    """
    try:
        code = request.args.get("code")
        if not code:
            logger.error("❌ ERROR: Missing authorization code in callback")
            return jsonify({"error": "Missing authorization code"}), 400

        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

        if not client_id or not client_secret or not redirect_uri:
            logger.error("❌ ERROR: Missing required environment variables")
            return jsonify({"error": "Missing required environment variables"}), 500

        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        logger.info(f"🔗 Sending token exchange request to {token_url} with payload: {payload}")

        response = requests.post(token_url, data=payload)
        if response.status_code != 200:
            logger.error(f"❌ ERROR: Failed to exchange code for tokens: {response.text}")
            return jsonify({"error": "Failed to exchange code for tokens"}), 500

        tokens = response.json()
        logger.info(f"✅ Token exchange successful: {tokens}")

        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            logger.warning("⚠️ WARNING: No refresh token received")
            return jsonify({"error": "No refresh token received"}), 400

        # Save the refresh token in the Users collection
        user_id = request.headers.get("User-ID")
        if not user_id:
            logger.error("❌ ERROR: Missing user ID in headers")
            return jsonify({"error": "Missing user ID"}), 400

        save_result = guest_repo.save_google_refresh_token(user_id, refresh_token)
        if save_result[1] != 200:
            logger.error(f"❌ ERROR: Failed to save refresh token: {save_result[0]['error']}")
            return jsonify({"error": "Failed to save refresh token"}), 500

        return jsonify({"message": "Google calendar connected successfully"}), 200

    except Exception as e:
        logger.exception("❌ ERROR: Failed to handle calendar callback")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


def send_email(to_email, subject, body, image_path=None):
    """
    Sends an email with optional inline image attachments.
    """
    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    # Add plain-text version
    plain_text = "This is the plain-text version of the email. Please view it in an HTML-compatible email client."
    msg.attach(MIMEText(plain_text, "plain"))

    # Attach the HTML content
    msg.attach(MIMEText(body, "html"))

    # Attach inline image if provided
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                img = MIMEImage(img_file.read(), _subtype="png")
                img.add_header("Content-ID", "<pod_manager_logo>")
                img.add_header("Content-Disposition", "inline", filename="PodManagerLogo.png")
                msg.attach(img)
            logger.info("✅ Attached inline image successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to attach image: {e}")

    try:
        logger.info(f"📡 Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            logger.info(f"🔐 Logging in as {EMAIL_USER}")
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
            logger.info(f"✅ Email successfully sent to {to_email}")
            return {"success": True}
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ Authentication failed: {e}")
        return {"error": "Authentication failed. Check your email credentials."}
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {e}")
        return {"error": str(e)}


def send_team_invite_email(
    email, invite_token, team_name=None, inviter_name=None, role=None
):
    """
    Sends an invitation email for a team membership with an inline logo.
    """
    # 🔹 Force LOCALHOST for debugging
    base_url = "http://127.0.0.1:8000"

    # Create the registration link with the invite token, team name, and role
    registration_link = f"{base_url}/register_team_member?token={invite_token}"

    # Add team name and role parameters if available
    if team_name:
        registration_link += f"&teamName={team_name}"

    # Add role parameter (using default if not provided)
    registration_link += f"&role={role}"

    # ✅ Log the generated URL before sending the email
    logger.info(f"🔗 Forced LOCALHOST invite URL: {registration_link} for {email}")

    subject = "You've been invited to join a team!"

    team_info = f"the team at {team_name}" if team_name else "a team"
    inviter_info = f" by {inviter_name}" if inviter_name else ""

    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center;">
                <img src="cid:pod_manager_logo" alt="PodManager Logo" style="max-width: 150px; margin-bottom: 20px;">
                <h2 style="color: #0056b3;">Team Invitation</h2>
                <p>Hello,</p>
                <p>You've been invited to join {team_info}{inviter_info}.</p>
                <p>To accept this invitation, please click the button below to register as a team member:</p>
                <p style="text-align: center;">
                    <a href="{registration_link}" style="display: inline-block;
                        padding: 12px 24px;
                        background-color: #FF8C00;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        font-weight: bold;">
                        Register as Team Member
                    </a>
                </p>
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="font-size: 14px; color: #666;">
                        If you did not expect this invitation, you can safely ignore this email.
                    </p>
                    <p style="font-size: 14px; color: #666;">
                        This invitation link will expire in 48 hours.
                    </p>
                </div>
            </div>
        </body>
    </html>
    """

    # Path to the PodManager logo
    image_path = "src/frontend/static/images/PodManagerLogo.png"

    # 🔹 Call send_email() with inline image support
    return send_email(email, subject, body, image_path=image_path)


def send_guest_invitation_email(guest_name, guest_email, guest_form_url, podcast_name):
    """
    Sends an invitation email to a guest with a link to the guest form.
    """
    try:
        # Render the email body using the guest-email.html template
        body = render_template(
            "guest-email/guest-email.html",
            guest_name=guest_name,
            guest_form_url=guest_form_url,
            podcast_name=podcast_name,
        )

        subject = f"You're Invited to Join {podcast_name} as a Guest!"
        return send_email(guest_email, subject, body)

    except Exception as e:
        logger.error(f"Failed to send guest invitation email: {e}", exc_info=True)
        return {"error": f"Failed to send guest invitation email: {str(e)}"}
