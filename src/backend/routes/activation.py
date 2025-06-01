from flask import Blueprint, request, current_app, jsonify, render_template, g, session
from pymongo import MongoClient
import os, secrets, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from dotenv import load_dotenv
from backend.services.rss_Service import RSSService
from backend.utils.token_utils import create_token_24h
import logging
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import random
from io import BytesIO
from backend.utils.blob_storage import upload_file_to_blob
from azure.storage.blob import BlobServiceClient

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

def send_activation_email(email, activation_link, podcast_name, rss_url):
    rss_service = RSSService()
    rss_data, status_code = rss_service.fetch_rss_feed(rss_url)
    artwork_url = None
    if status_code == 200 and rss_data:
        artwork_url = rss_data.get("imageUrl")
    if not artwork_url or not artwork_url.startswith("http"):
        artwork_url = "https://podmanager.app/static/images/default.png"

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
        token = create_token_24h({
            "email": email,
            "rss_url": rss_url,
            "podcast_title": podcast_title
        })
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
        token = create_token_24h({
            "email": email_param,
            "rss_url": rss_param,
            "podcast_title": title_param
        })
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
    user_id = g.get('user_id')
    logger.info(f"Attempting to fetch initial podprofile data for user_id (ownerId): {user_id}")

    initial_rss_url = None
    initial_podcast_id = None
    initial_podcast_title = None

    if user_id:
        user_accounts = list(db["Accounts"].find({"ownerId": str(user_id)}, {"_id": 1}))
        if user_accounts:
            account_ids = [str(acc["_id"]) for acc in user_accounts]
            logger.info(f"Found account IDs for owner {user_id}: {account_ids}")
            
            query_criteria = {
                "accountId": {"$in": account_ids},
                "isImported": True,
                "rssFeed": {"$exists": True, "$ne": None, "$ne": ""}
            }
            logger.info(f"Querying Podcasts collection with criteria: {query_criteria}")

            podcast = podcasts_collection.find_one(query_criteria, sort=[("createdAt", 1)]) 
            
            if podcast:
                logger.info(f"Found podcast for prefill: {podcast}")
                initial_rss_url = podcast.get("rssFeed")
                initial_podcast_id = str(podcast.get("_id"))
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
        "initial_podcast_title": initial_podcast_title
    })

def get_blob_content(container_name, blob_path):
    """Read a blob directly from Azure Blob Storage without downloading to a file"""
    try:
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            logger.error("AZURE_STORAGE_CONNECTION_STRING environment variable not set.")
            return None
            
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
        
        # Download blob content directly to memory
        download_stream = blob_client.download_blob()
        content = download_stream.readall()
        
        logger.info(f"Successfully read blob: {blob_path}")
        return content
    except Exception as e:
        logger.error(f"Error reading blob {blob_path}: {e}", exc_info=True)
        return None

def load_activated_emails():
    """Load the activated emails tracking JSON from blob storage"""
    try:
        logger.info(f"Loading activated emails record from blob: {ACTIVATED_JSON_BLOB_PATH}")
        blob_content = get_blob_content(BLOB_CONTAINER, ACTIVATED_JSON_BLOB_PATH)
        
        if not blob_content:
            logger.info("No existing activated emails record found. Creating new one.")
            return {
                "last_sent_date": "",
                "emails_sent": []
            }
        
        data = json.loads(blob_content.decode('utf-8'))
        return data
    
    except Exception as e:
        logger.error(f"Error loading activated emails: {e}", exc_info=True)
        # Return a fresh tracking object if load fails
        return {
            "last_sent_date": "",
            "emails_sent": []
        }

def save_activated_emails(data):
    """Save the activated emails tracking JSON to blob storage"""
    try:
        logger.info(f"Saving activated emails record to blob: {ACTIVATED_JSON_BLOB_PATH}")
        
        # Update the last sent date
        data["last_sent_date"] = datetime.now().isoformat()
        
        # Convert to JSON string
        json_data = json.dumps(data, indent=2)
        
        # Upload to blob storage
        json_bytes = BytesIO(json_data.encode('utf-8'))
        upload_url = upload_file_to_blob(
            container_name=BLOB_CONTAINER,
            blob_path=ACTIVATED_JSON_BLOB_PATH,
            file=json_bytes,
            content_type="application/json"
        )
        
        if not upload_url:
            logger.error("Failed to save activated emails record to blob storage")
            return False
            
        return True
    
    except Exception as e:
        logger.error(f"Error saving activated emails: {e}", exc_info=True)
        return False

@podprofile_initial_bp.route('/podprofile_initial', methods=["GET"])
def podprofile_initial():
    """Renders the initial podprofile page."""
    try:
        return render_template('podprofile/podprofile_initial.html')
    except Exception as e:
        logger.error(f"Error rendering podprofile_initial page: {e}", exc_info=True)
        return jsonify({"error": "Failed to render podprofile initial page"}), 500

@activation_bp.route("/send_activation_emails", methods=["POST"])
def send_activation_emails():
    data = request.get_json() or {}
    num_emails = int(data.get("num_emails", 30))  # Default to 30 if not specified
    
    try:
        # Load existing activated emails record
        activated_record = load_activated_emails()
        emails_already_sent = set(activated_record.get("emails_sent", []))
        logger.info(f"Found {len(emails_already_sent)} previously sent emails")
        
        # Load scraped XML from blob storage
        xml_content = get_blob_content(BLOB_CONTAINER, SCRAPED_XML_BLOB_PATH)
        if not xml_content:
            return jsonify({"error": "Failed to read scraped XML from blob storage"}), 500
        
        # Parse the XML
        root = ET.fromstring(xml_content)
        
        # Extract email addresses from XML
        user_elements = root.findall(".//user")
        all_emails = [
            {
                "email": user.find("email").text,
                "name": user.find("name").text if user.find("name") is not None else "",
                "id": user.attrib.get("id", ""),
                "podcast": user.find("podcast").text if user.find("podcast") is not None else "Your Podcast"
            }
            for user in user_elements
            if user.find("email") is not None and user.find("email").text
        ]
        
        # Filter out already sent emails
        emails_to_send = [
            email_data for email_data in all_emails 
            if email_data["email"] not in emails_already_sent
        ]
        
        # Check if we have any new emails to send
        if not emails_to_send:
            logger.info("No new emails to send")
            return jsonify({
                "message": "No new emails to send",
                "emails_sent": 0,
                "total_processed": len(all_emails),
                "already_sent": len(emails_already_sent)
            }), 200
        
        # Limit to requested number
        emails_to_send = emails_to_send[:num_emails]
        logger.info(f"Preparing to send activation emails to {len(emails_to_send)} recipients")
        
        # Generate activation codes and send emails
        success_count = 0
        newly_sent_emails = []
        
        for email_data in emails_to_send:
            try:
                # Generate a random activation code
                activation_code = ''.join(random.choices('0123456789', k=6))
                
                # Prepare email content
                subject = "Your PodManager Activation Code"
                html_content = f"""
                <html>
                <body>
                    <h2>Welcome to PodManager!</h2>
                    <p>Hello {email_data['name']},</p>
                    <p>Your activation code is: <strong>{activation_code}</strong></p>
                    <p>Use this code to activate your account for {email_data['podcast']} and start managing your podcasts.</p>
                    <p>Best regards,<br>The PodManager Team</p>
                </body>
                </html>
                """
                
                # Send the email
                result = send_email(
                    to_email=email_data["email"],
                    subject=subject,
                    body=html_content,
                    is_html=True
                )
                
                if result:
                    success_count += 1
                    newly_sent_emails.append(email_data["email"])
                    logger.info(f"Successfully sent activation email to: {email_data['email']}")
                else:
                    logger.error(f"Failed to send activation email to: {email_data['email']}")
            
            except Exception as e:
                logger.error(f"Error sending activation email to {email_data['email']}: {str(e)}")
        
        # Update our tracking record
        activated_record["emails_sent"].extend(newly_sent_emails)
        save_success = save_activated_emails(activated_record)
        
        if not save_success:
            logger.warning("Failed to save updated activated emails record")
        
        return jsonify({
            "message": f"Successfully sent {success_count} activation emails",
            "emails_sent": success_count,
            "total_processed": len(all_emails),
            "already_sent": len(emails_already_sent)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in send_activation_emails: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to send activation emails: {str(e)}"}), 500

@activation_bp.route("/activation/invite", methods=["POST"])
def activation_invite():
    """
    API endpoint for sending a single activation invitation email.
    Expects a JSON payload with 'email', 'name', and 'podcast' fields.
    """
    try:
        logger.info(f"Activation invite request received")
        data = request.get_json()
        if not data or not data.get("email"):
            return jsonify({"success": False, "error": "Email address is required"}), 400

        email = data.get("email")
        name = data.get("name", "")
        podcast = data.get("podcast", "Your Podcast")
        
        logger.info(f"Processing activation invite for: {email}, Podcast: {podcast}")
        
        # Check if email was already sent
        activated_record = load_activated_emails()
        emails_already_sent = set(activated_record.get("emails_sent", []))
        
        if email in emails_already_sent:
            logger.info(f"Email {email} already received an invite")
            return jsonify({
                "success": False, 
                "message": "Email already invited"
            }), 200
            
        # Generate activation code
        activation_code = ''.join(random.choices('0123456789', k=6))
        
        # Prepare email content
        subject = f"Your {podcast} PodManager Activation"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #ff8c00;">Welcome to PodManager!</h2>
                <p>Hello {name},</p>
                <p>You've been invited to use PodManager for <strong>{podcast}</strong>!</p>
                <p>Your activation code is: <strong style="font-size: 18px; color: #ff8c00;">{activation_code}</strong></p>
                <p>Use this code to activate your account and start managing your podcast more efficiently.</p>
                <p>Best regards,<br>The PodManager Team</p>
            </div>
        </body>
        </html>
        """
        
        # Send the email
        result = send_email(
            to_email=email,
            subject=subject,
            body=html_content,
            is_html=True
        )
        
        if result:
            # Update tracking record
            activated_record["emails_sent"].append(email)
            save_activated_emails(activated_record)
            
            logger.info(f"Successfully sent activation invite to: {email}")
            return jsonify({
                "success": True,
                "message": f"Activation invite sent to {email}"
            }), 200
        else:
            logger.error(f"Email sending failed for: {email}")
            return jsonify({
                "success": False,
                "error": "Failed to send email"
            }), 500
        
    except Exception as e:
        logger.error(f"Error processing activation invite: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }), 500

@activation_bp.route("/reset_activation_tracking", methods=["POST"])
def reset_activation_tracking():
    """Endpoint to reset the activation tracking (for admin use)"""
    try:
        # Create a fresh tracking object
        fresh_tracking = {
            "last_sent_date": "",
            "emails_sent": []
        }
        
        # Save it to blob storage
        save_success = save_activated_emails(fresh_tracking)
        
        if save_success:
            return jsonify({"message": "Activation tracking reset successfully"}), 200
        else:
            return jsonify({"error": "Failed to reset activation tracking"}), 500
            
    except Exception as e:
        logger.error(f"Error resetting activation tracking: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to reset activation tracking: {str(e)}"}), 500

@activation_bp.route("/activation_stats", methods=["GET"])
def activation_stats():
    """Get statistics about activation emails"""
    try:
        # Load existing activated emails record
        activated_record = load_activated_emails()
        emails_sent = activated_record.get("emails_sent", [])
        last_sent_date = activated_record.get("last_sent_date", "")
        
        # Load scraped XML to get total count
        xml_content = get_blob_content(BLOB_CONTAINER, SCRAPED_XML_BLOB_PATH)
        if not xml_content:
            return jsonify({"error": "Failed to read scraped XML from blob storage"}), 500
        
        # Parse the XML
        root = ET.fromstring(xml_content)
        
        # Count total emails in XML
        user_elements = root.findall(".//user")
        total_emails = len([
            user for user in user_elements
            if user.find("email") is not None and user.find("email").text
        ])
        
        return jsonify({
            "total_emails": total_emails,
            "emails_sent": len(emails_sent),
            "emails_remaining": total_emails - len(emails_sent),
            "last_sent_date": last_sent_date,
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting activation stats: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to get activation stats: {str(e)}"}), 500
