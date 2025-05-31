from flask import Blueprint, request, jsonify, current_app, render_template
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from backend.utils.email_utils import send_email
import logging
import random
from io import BytesIO
from backend.utils.blob_storage import upload_file_to_blob
from azure.storage.blob import BlobServiceClient

# Configure logging
logger = logging.getLogger(__name__)

# Define blueprints
activation_bp = Blueprint('activation_bp', __name__)
podprofile_initial_bp = Blueprint('podprofile_initial_bp', __name__)

# Constants
BLOB_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "podmanagerfiles")
SCRAPED_XML_BLOB_PATH = "activate/scraped.xml"
ACTIVATED_JSON_BLOB_PATH = "activate/activated_emails.json"

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

@activation_bp.route("/send_activation_emails", methods=["POST"])
def send_activation_emails():
    data = request.get_json() or {}
    num_emails = int(data.get("num_emails", 30))  # Default to 30 if not specified
    
    try:
        # Load existing activated emails record
        activated_record = load_activated_emails()
        emails_already_sent = set(activated_record.get("emails_sent", []))
        logger.info(f"Found {len(emails_already_sent)} previously sent emails")
        
        # Read XML directly from blob storage
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
                "id": user.attrib.get("id", "")
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
                    <p>Use this code to activate your account and start managing your podcasts.</p>
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
        
        # Read XML directly from blob storage to get total count
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

@podprofile_initial_bp.route('/podprofile_initial', methods=["GET"])
def podprofile_initial():
    """Renders the initial podprofile page."""
    try:
        return render_template('podprofile/podprofile_initial.html')
    except Exception as e:
        logger.error(f"Error rendering podprofile_initial page: {e}", exc_info=True)
        return jsonify({"error": "Failed to render podprofile initial page"}), 500
