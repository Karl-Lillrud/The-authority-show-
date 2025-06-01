import os
import xml.etree.ElementTree as ET
import logging
import requests
from dotenv import load_dotenv
from datetime import datetime
import json
from io import BytesIO
from backend.utils.email_utils import send_activation_email
from backend.utils.blob_storage import get_blob_content, upload_file_to_blob

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip('/')
BLOB_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "podmanagerfiles")
SCRAPED_XML_BLOB_PATH = "activate/scraped.xml"
ACTIVATED_JSON_BLOB_PATH = "activate/activated_emails.json"

def load_podcasts_from_blob():
    """Load podcasts from the XML file in blob storage."""
    podcasts = []
    try:
        # Get XML data from blob storage
        xml_content = get_blob_content(BLOB_CONTAINER, SCRAPED_XML_BLOB_PATH)
        if not xml_content:
            logger.error(f"XML data not found in blob storage at {SCRAPED_XML_BLOB_PATH}")
            return []
            
        # Parse XML from the content
        root = ET.fromstring(xml_content)
        
        for podcast_elem in root.findall("podcast"):
            title = podcast_elem.findtext("title")
            email_element = podcast_elem.find("emails/email")
            email = email_element.text if email_element is not None else None
            rss_feed = podcast_elem.findtext("rss")
            if title and email and rss_feed:
                podcasts.append({"title": title, "email": email, "rss_feed": rss_feed})
            else:
                logger.warning(f"Skipping podcast entry due to missing data: Title={title}, Email={email}, RSS={rss_feed}")
        logger.info(f"Loaded {len(podcasts)} podcasts from blob storage XML")
    except ET.ParseError:
        logger.error(f"Error parsing XML from blob storage")
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading XML: {e}", exc_info=True)
    return podcasts

def load_activated_emails():
    """Load the list of emails that have already been activated."""
    try:
        logger.info(f"Loading activated emails record from blob: {ACTIVATED_JSON_BLOB_PATH}")
        blob_content = get_blob_content(BLOB_CONTAINER, ACTIVATED_JSON_BLOB_PATH)
        
        if not blob_content:
            logger.info("No existing activated emails record found. Will create a new one when first emails are sent.")
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

def get_podcast_logo_from_rss(rss_url):
    """Fetch podcast logo from RSS feed URL"""
    try:
        if not rss_url:
            return None
            
        from backend.services.rss_Service import RSSService
        rss_service = RSSService()
        rss_data, status = rss_service.fetch_rss_feed(rss_url)
        
        if status == 200 and rss_data and rss_data.get("imageUrl"):
            logo_url = rss_data.get("imageUrl")
            logger.info(f"Successfully fetched podcast logo from RSS: {logo_url}")
            return logo_url
        else:
            logger.warning(f"No logo found in RSS feed: {rss_url}")
            return None
    except Exception as e:
        logger.error(f"Error fetching podcast logo from RSS: {e}", exc_info=True)
        return None

def process_activation_emails(num_emails=5):
    """
    Process and send activation emails in a batch.
    This function is designed to be called by the scheduler at 5 AM.
    
    Args:
        num_emails (int): Maximum number of emails to send in this batch
        
    Returns:
        dict: Result of the operation with keys:
            - success: Boolean indicating success
            - message: Description of results
            - emails_sent: Number of emails sent
            - total_processed: Total podcasts processed
    """
    logger.info(f"Starting activation email processing (batch size: {num_emails})")
    try:
        # Load existing activated emails record
        activated_record = load_activated_emails()
        emails_already_sent = set(activated_record.get("emails_sent", []))
        logger.info(f"Found {len(emails_already_sent)} previously sent emails")
        
        # Load podcasts data from XML blob
        podcasts_to_process = load_podcasts_from_blob()
        if not podcasts_to_process:
            logger.info("No podcasts to process. Exiting.")
            return {"success": False, "message": "No podcasts to process", "emails_sent": 0}

        emails_sent_successfully = 0
        total_processed = 0
        processed_emails_in_current_run = set()  # Keep track of processed emails in this run

        # Filter out already processed emails
        podcasts_to_process = [
            podcast for podcast in podcasts_to_process
            if podcast.get("email") and podcast.get("email") not in emails_already_sent
        ]
        
        # Limit to the batch size
        podcasts_to_process = podcasts_to_process[:num_emails]
        
        for podcast_data in podcasts_to_process:
            total_processed += 1
            email = podcast_data.get("email")
            rss_url = podcast_data.get("rss_feed")
            podcast_title = podcast_data.get("title")

            if not email or not rss_url or not podcast_title:
                logger.warning(f"Skipping entry due to incomplete data: {podcast_data}")
                continue

            if email in processed_emails_in_current_run:
                logger.info(f"Skipping duplicate email in current run: {email} for podcast: {podcast_title}")
                continue

            try:
                logger.info(f"Processing activation for: {email}, Podcast: {podcast_title}, RSS: {rss_url}")
                
                # Get podcast logo from RSS if available
                artwork_url = get_podcast_logo_from_rss(rss_url) 
                
                # Generate activation link
                activation_link = f"{API_BASE_URL}/signin?email={email}"
                
                # Send activation email using email_utils
                result = send_activation_email(email, activation_link, podcast_title, artwork_url)
                
                if result.get("success", False):
                    logger.info(f"Successfully sent activation email to {email}")
                    emails_sent_successfully += 1
                    processed_emails_in_current_run.add(email)
                    
                    # Add to tracking list
                    activated_record["emails_sent"].append(email)
                else:
                    logger.error(f"Failed to send activation email to {email}: {result.get('error', 'Unknown error')}")

            except Exception as e:
                logger.error(f"Failed to process activation for {email}: {e}", exc_info=True)

        # Update tracking record if any emails were sent
        if processed_emails_in_current_run:
            save_success = save_activated_emails(activated_record)
            if not save_success:
                logger.warning("Failed to save updated activated emails record")

        logger.info(f"Activation process finished. Processed {total_processed} entries. Successfully sent {emails_sent_successfully} emails.")
        
        return {
            "success": True,
            "message": f"Successfully sent {emails_sent_successfully} activation emails",
            "emails_sent": emails_sent_successfully,
            "total_processed": total_processed
        }
        
    except Exception as e:
        logger.error(f"Error processing activation emails: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to process activation emails: {str(e)}",
            "emails_sent": 0,
            "total_processed": 0
        }

def get_activation_stats():
    """Get statistics about activation emails"""
    try:
        # Load existing activated emails record
        activated_record = load_activated_emails()
        emails_sent = activated_record.get("emails_sent", [])
        last_sent_date = activated_record.get("last_sent_date", "")
        
        # Load all podcasts from blob
        all_podcasts = load_podcasts_from_blob()
        total_podcasts = len(all_podcasts)
        
        return {
            "total_podcasts": total_podcasts,
            "emails_sent": len(emails_sent),
            "podcasts_remaining": total_podcasts - len(emails_sent),
            "last_sent_date": last_sent_date,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting activation stats: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to get activation stats: {str(e)}"
        }

def main():
    """Legacy entry point for manual running"""
    logger.info("Starting activation script...")
    result = process_activation_emails(5)  # Process up to 5 emails in one batch
    logger.info(f"Activation script completed with result: {result}")

if __name__ == "__main__":
    main()
