from flask import Blueprint, request, current_app, jsonify, render_template, g, session
from pymongo import MongoClient
import os, secrets, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from dotenv import load_dotenv
from backend.services.rss_Service import RSSService
from backend.services.authService import AuthService
import logging

load_dotenv() 
activation_bp = Blueprint("activation", __name__)
podprofile_initial_bp = Blueprint("podprofile_initial", __name__)
logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGODB_URI") 
MONGO_DB_NAME = "Podmanager"

# Email configuration checks
EMAIL_SENDER = os.getenv("EMAIL_USER") # Use EMAIL_USER for sending
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")
SMTP_SERV = os.getenv("SMTP_SERVER")
SMTP_PRT = os.getenv("SMTP_PORT", 587)

if not all([EMAIL_SENDER, EMAIL_PASS, SMTP_SERV]):
    logger.critical("CRITICAL: Email environment variables (EMAIL_USER, EMAIL_PASSWORD, SMTP_SERVER) are not fully set.")

if not MONGO_URI:
    logger.critical("CRITICAL: MONGODB_URI environment variable not set.") 
    raise ValueError("MONGODB_URI environment variable not set. Application cannot start.") 

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
podcasts_collection = db["Podcasts"]
auth_service = AuthService()

def send_activation_email(email, activation_link, podcast_name, rss_url):
    rss_service = RSSService()
    rss_data, status_code = rss_service.fetch_rss_feed(rss_url)
    artwork_url = None
    if status_code == 200 and rss_data:
        artwork_url = rss_data.get("imageUrl")
    if not artwork_url or not artwork_url.startswith("http"):
        artwork_url = "https://podmanager.app/static/images/default-artwork.png"

    try:
        html_body = render_template(
            "emails/activate_email.html",
            activation_link=activation_link,
            podcast_name=podcast_name,
            artwork_url=artwork_url
        )
    except Exception as e:
        logger.error(f"Error rendering email template: {e}", exc_info=True)
        html_body = f"""
        <html><body>
            <p>Hi,</p>
            <p>Please activate your account using this link: <a href="{activation_link}">Activate Account</a></p>
            <p>Podcast: {podcast_name}</p>
        </body></html>
        """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Exclusive Access to PodManager—Activate Your Account Today! 🚀"
    # Format the "From" header to "PodManager.ai <contact@podmanager.ai>"
    msg["From"] = formataddr(("PodManager.ai", EMAIL_SENDER))
    msg["To"] = email

    plain_text_body = f"""
    Hi,

    We're thrilled to offer you exclusive early access to PodManager!
    Activate your account for podcast "{podcast_name}" here: {activation_link}

    Thanks,
    The PodManager Team
    """
    part1 = MIMEText(plain_text_body, "plain")
    part2 = MIMEText(html_body, "html")

    msg.attach(part1)
    msg.attach(part2)

    try:
        smtp_port_int = int(SMTP_PRT)
        with smtplib.SMTP(SMTP_SERV, smtp_port_int) as server:
            server.set_debuglevel(0)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_SENDER, EMAIL_PASS)
            server.send_message(msg)
        logger.info(f"✅ Activation email sent to {email} with link: {activation_link}")
    except Exception as e:
        logger.error(f"❌ Email failed for {email}: {e}", exc_info=True)

@activation_bp.route("/invite", methods=["POST"])
def invite_user_via_api():
    data = request.get_json()
    if not data or "email" not in data or "rss_url" not in data or "podcast_title" not in data:
        return jsonify({"error": "Missing email, rss_url, or podcast_title"}), 400

    email = data["email"]
    rss_url = data["rss_url"]
    podcast_title = data["podcast_title"]

    try:
        if not current_app.config.get("SECRET_KEY"):
            logger.error("SECRET_KEY is not configured in the application.")
            return jsonify({"error": "Server configuration error for token generation"}), 500

        token = auth_service.generate_activation_token(email, rss_url, podcast_title, current_app.config["SECRET_KEY"])
        base_url = request.host_url.rstrip('/')
        activation_link = f"{base_url}/activate?token={token}" 
        
        logger.info(f"Generated activation link for {email} via API: {activation_link}") 
        send_activation_email(email, activation_link, podcast_title, rss_url)
        return jsonify({
            "message": f"✅ Activation invitation sent to {email}",
            "activation_link": activation_link 
        }), 200
    except Exception as e:
        logger.error(f"Error during invite process for {email}: {e}", exc_info=True)
        return jsonify({"error": "Failed to send activation invite"}), 500

@activation_bp.route("/invite_manual_test", methods=["GET"])
def invite_user_manual_test():
    email_param = request.args.get("email")
    rss_param = request.args.get("rss_url")
    title_param = request.args.get("podcast_title")

    if not email_param or not rss_param or not title_param:
        return "Missing query parameters: email, rss_url, podcast_title", 400

    try:
        if not current_app.config.get("SECRET_KEY"):
            logger.error("SECRET_KEY is not configured in the application.")
            return "Server configuration error for token generation", 500
            
        token = auth_service.generate_activation_token(email_param, rss_param, title_param, current_app.config["SECRET_KEY"])
        base_url = request.host_url.rstrip('/')
        activation_link = f"{base_url}/activate?token={token}"
        
        logger.info(f"Generated manual activation link for {email_param}: {activation_link}") 
        send_activation_email(email_param, activation_link, title_param, rss_param)
        return f"✅ Invitation sent to {email_param}"
    except Exception as e:
        logger.error(f"Error during manual invite test for {email_param}: {e}", exc_info=True)
        return "Failed to send activation invite", 500

@podprofile_initial_bp.route('/initial', methods=['GET'])
def get_initial_podprofile_data():
    user_id = g.get('user_id') # This is Users._id (ownerId for accounts)
    logger.info(f"Attempting to fetch initial podprofile data for user_id (ownerId): {user_id}")

    initial_rss_url = None
    initial_podcast_id = None
    initial_podcast_title = None

    if user_id:
        # Find accounts owned by this user
        user_accounts = list(db["Accounts"].find({"ownerId": str(user_id)}, {"_id": 1}))
        if user_accounts:
            account_ids = [str(acc["_id"]) for acc in user_accounts]
            logger.info(f"Found account IDs for owner {user_id}: {account_ids}")
            
            query_criteria = {
                "accountId": {"$in": account_ids},
                "isImported": True,
                "rssFeed": {"$exists": True, "$ne": None, "$ne": ""} # Ensure rssFeed is valid
            }
            logger.info(f"Querying Podcasts collection with criteria: {query_criteria}")

            # Find the first imported podcast linked to any of these accounts
            # Sort by createdAt to get the earliest one if multiple imported podcasts exist
            podcast = podcasts_collection.find_one(query_criteria, sort=[("createdAt", 1)]) 
            
            if podcast:
                logger.info(f"Found podcast for prefill: {podcast}")
                initial_rss_url = podcast.get("rssFeed")
                initial_podcast_id = str(podcast.get("_id"))
                # Prefer 'title', fallback to 'podName'
                initial_podcast_title = podcast.get("title") or podcast.get("podName") 
                if not initial_rss_url:
                    logger.warning(f"Podcast found (ID: {initial_podcast_id}) but 'rssFeed' is missing or empty.")
                if not initial_podcast_title:
                    logger.warning(f"Podcast found (ID: {initial_podcast_id}) but 'title' and 'podName' are missing or empty.")
            else:
                logger.info(f"No imported podcast found matching criteria for account IDs: {account_ids}")
        else:
            logger.info(f"No accounts found for ownerId: {user_id}")
    else:
        logger.warning("No user_id found in g context for fetching initial podprofile data.")

    logger.info(f"Returning Initial RSS: {initial_rss_url}, Podcast ID: {initial_podcast_id}, Podcast Title: {initial_podcast_title} for user_id (ownerId): {user_id}")

    return jsonify({
        "initial_rss_url": initial_rss_url,
        "initial_podcast_id": initial_podcast_id,
        "initial_podcast_title": initial_podcast_title  # Include the title in the response
    })