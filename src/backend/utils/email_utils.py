import smtplib
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from dotenv import load_dotenv
from flask import render_template, Blueprint, request, jsonify, url_for, redirect
import urllib.parse
import requests
from backend.repository.guest_repository import GuestRepository
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from backend.utils.config_utils import get_client_secret
from backend.services.activity_service import ActivityService  # Add this import
from pymongo import MongoClient
from backend.database.mongo_connection import collection

# Load environment variables once
load_dotenv(override=True)

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["Podmanager"]
podcasts = db["Podcasts"]


EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
CLIENT_SECRET = get_client_secret()
TOKEN_FILE = os.getenv("TOKEN_FILE")
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
        refresh_token = data.get("refreshToken")
        user_id = request.headers.get("User-ID")

        if not refresh_token or not user_id:
            return jsonify({"error": "Missing refresh token or user ID"}), 400

        result = collection.database.Users.update_one(
            {"_id": user_id}, {"$set": {"googleRefresh": refresh_token}}, upsert=True
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
        return redirect(auth_url)
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
        client_secret = CLIENT_SECRET
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

        logger.info(f"🔗 Sending token exchange request to {token_url}")
        response = requests.post(token_url, data=payload)
        if response.status_code != 200:
            logger.error(
                f"❌ ERROR: Failed to exchange code for tokens: {response.text}"
            )
            return jsonify({"error": "Failed to exchange code for tokens"}), 500

        tokens = response.json()
        logger.info(f"✅ Token exchange successful")
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            logger.warning("⚠️ WARNING: No refresh token received")
            return jsonify({"error": "No refresh token received"}), 400

        user_id = request.headers.get("User-ID")
        if not user_id:
            logger.error("❌ ERROR: Missing user ID in headers")
            return jsonify({"error": "Missing user ID"}), 400

        save_result = guest_repo.save_google_refresh_token(user_id, refresh_token)
        if save_result[1] != 200:
            logger.error(
                f"❌ ERROR: Failed to save refresh token: {save_result[0]['error']}"
            )
            return jsonify({"error": "Failed to save refresh token"}), 500

        return jsonify({"message": "Google calendar connected successfully"}), 200

    except Exception as e:
        logger.exception("❌ ERROR: Failed to handle calendar callback")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


def get_oauth2_credentials():
    """
    Get OAuth2 credentials for Gmail API.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


def send_email(to_email, subject, body, image_path=None):
    """
    Sends an email using Microsoft 365 SMTP server.
    """
    try:
        # Create the email message
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                img = MIMEImage(img_file.read(), _subtype="png")
                img.add_header("Content-ID", "<pod_manager_logo>")
                img.add_header(
                    "Content-Disposition", "inline", filename="PodManagerLogo.png"
                )
                msg.attach(img)

        # Connect to Microsoft 365 SMTP server
        logger.info(
            f"📡 Connecting to Microsoft 365 SMTP server {SMTP_SERVER}:{SMTP_PORT}"
        )
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            logger.info(f"🔐 Logging in as {EMAIL_USER}")
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
            logger.info(f"✅ Email successfully sent to {to_email}")
            return {"success": True}
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {e}", exc_info=True)
        return {"error": f"Failed to send email: {str(e)}"}


def send_login_email(email, login_link):
    """
    Sends a login link email to the user and prints the link to the terminal.
    """
    try:
        subject = "Your login link for PodManager"
        body = f"""
        <html>
            <body>
                <p>Hello,</p>
                <p>Click the link below to log in to your PodManager account:</p>
                <a href="{login_link}" style="color: #ff7f3f; text-decoration: none;">Log in</a>
                <p>This link is valid for 10 minutes. If you did not request this, please ignore this email.</p>
                <p>Best regards,<br>PodManager Team</p>
            </body>
        </html>
        """
        logger.info(f"📧 Preparing to send login email to {email}")

        # Print the login link in pink color to the terminal
        print(f"\033[95mLogin link for {email}: {login_link}\033[0m", flush=True)

        result = send_email(email, subject, body)
        if result.get("success"):
            logger.info(f"✅ Login email sent successfully to {email}")
            # --- Log activity for login email sent ---
            try:
                user = collection.database.Users.find_one(
                    {"email": email.lower().strip()}
                )
                if user:
                    ActivityService().log_activity(
                        user_id=str(user["_id"]),
                        activity_type="login_email_sent",
                        description=f"Login email sent to {email}",
                        details={"email": email},
                    )
            except Exception as act_err:
                logger.error(
                    f"Failed to log login_email_sent activity: {act_err}", exc_info=True
                )
            # --- End activity log ---
        else:
            logger.error(
                f"❌ Failed to send login email to {email}: {result.get('error')}"
            )
        return result
    except Exception as e:
        logger.error(
            f"❌ Error while sending login email to {email}: {e}", exc_info=True
        )
        return {"error": f"Error while sending login email: {str(e)}"}



def send_team_invite_email(
    email, invite_token, team_name=None, inviter_name=None, role=None
):
    """
    Sends an invitation email for a team membership with an inline logo.
    """
    # Use API_BASE_URL from environment variables, fallback to localhost
    base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    registration_link = f"{base_url}/register_team_member?token={invite_token}"
    if team_name:
        registration_link += f"&teamName={urllib.parse.quote(team_name)}"
    if role:
        registration_link += f"&role={urllib.parse.quote(role)}"

    logger.info(f"🔗 Team invite URL: {registration_link} for {email}")
    print(f"Team invite link for {email}: {registration_link}")

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

    image_path = "src/frontend/static/images/PodManagerLogo.png"
    result = send_email(email, subject, body, image_path=image_path)
    # --- Log activity for team invite email sent ---
    try:
        user = collection.database.Users.find_one({"email": email.lower().strip()})
        if user:
            ActivityService().log_activity(
                user_id=str(user["_id"]),
                activity_type="team_invite_email_sent",
                description=f"Team invite email sent to {email}",
                details={"email": email, "teamName": team_name, "role": role},
            )
    except Exception as act_err:
        logger.error(
            f"Failed to log team_invite_email_sent activity: {act_err}", exc_info=True
        )
    # --- End activity log ---
    return result


def send_guest_invitation_email(guest_name, guest_email, guest_form_url, podcast_name):
    """
    Sends an invitation email to a guest with a link to the guest form.
    """
    try:
        body = render_template(
            "guest-email/guest-email.html",
            guest_name=guest_name,
            guest_form_url=guest_form_url,
            podcast_name=podcast_name,
        )
        subject = f"You're Invited to Join {podcast_name} as a Guest!"
        result = send_email(guest_email, subject, body)
        # --- Log activity for guest invite email sent ---
        try:
            user = collection.database.Users.find_one(
                {"email": guest_email.lower().strip()}
            )
            if user:
                ActivityService().log_activity(
                    user_id=str(user["_id"]),
                    activity_type="guest_invite_email_sent",
                    description=f"Guest invitation email sent to {guest_email}",
                    details={"guestName": guest_name, "podcastName": podcast_name},
                )
        except Exception as act_err:
            logger.error(
                f"Failed to log guest_invite_email_sent activity: {act_err}",
                exc_info=True,
            )
        # --- End activity log ---
        return result
    except Exception as e:
        logger.error(f"Failed to send guest invitation email: {e}", exc_info=True)
        print(
            f"Guest invitation email could not be sent to {guest_email}. Content:\nSubject: {subject}\nBody: {body}"
        )
        return {"error": f"Failed to send guest invitation email: {str(e)}"}


def send_activation_email(email, activation_link, podcast_name, artwork_url=None):
    """
    Sends an activation email to the user with a link to activate their account.
    """
    html = f"""
    <html>
        <body>
            <p>Hi,</p>
            <p>We're thrilled to offer you exclusive early access to <strong>PodManager</strong>, 
            the ultimate tool built to simplify podcasting for creators like you!</p>
            <p>We’ve already prepared your account. Just activate it to start unlocking the full potential of PodManager:</p>
            <p><a href="{activation_link}" style="color: #ff7f3f; text-decoration: none;">Activate Your Account Now</a></p>
        </body>
    </html>
    """

    msg = MIMEText(html, "html")
    msg["Subject"] = "Exclusive Access to PodManager—Activate Your Account Today! 🚀"
    msg["From"] = os.getenv("ACTIVATION_EMAIL")
    msg["To"] = email

    try:
        with smtplib.SMTP(
            os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))
        ) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(
                os.getenv("ACTIVATION_EMAIL"), os.getenv("ACTIVATION_PASSWORD")
            )
            server.send_message(msg)
        logger.info(f"✅ Activation email sent to {email}")
    except Exception as e:
        logger.error(
            f"❌ Failed to send activation email to {email}: {e}", exc_info=True
        )


@google_calendar_bp.route("/activation/invite", methods=["GET"])
def invite_user():
    """
    Sends an activation email to a user for their podcast account.
    """
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Missing email parameter"}), 400

        podcast = collection.database.Podcasts.find_one({"emails": email})
        if not podcast:
            return jsonify({"error": "No podcast found for the given email"}), 404

        base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
        activation_link = f"{base_url}/signin?email={email}"
        send_activation_email(
            email, activation_link, podcast["title"], podcast.get("artwork_url", "")
        )

        return jsonify({"message": f"Activation email sent to {email}"}), 200
    except Exception as e:
        logger.error(f"❌ Failed to send activation email: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
