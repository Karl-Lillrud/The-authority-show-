import os
import logging
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from flask import render_template
from backend.database.mongo_connection import collection
from backend.utils.email_utils import send_email
from backend.repository.guest_repository import GuestRepository
from backend.repository.episode_repository import EpisodeRepository

# Added imports for new scheduled job
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables for the new job
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))  # Ensure .env is loaded

# Define the path for the sent emails file
SENT_EMAILS_FILE = os.path.join(os.path.dirname(__file__), "sent_emails.json")
XML_FILE_PATH_FOR_ACTIVATION = os.getenv("ACTIVATION_XML_FILE_PATH", "../scraped.xml")  # From activate.py
API_BASE_URL_FOR_ACTIVATION = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip('/')  # From activate.py

scheduler = BackgroundScheduler(daemon=True)
guest_repo = GuestRepository()
episode_repo = EpisodeRepository()


def render_email_content(
    trigger_name,
    guest,
    episode,
    social_network=None,
    guest_email=None,
    podName=None,
    link=None,
    audio_url=None,
):
    try:
        template_path = f"emails/{trigger_name}_email.html"
        email_body = render_template(
            template_path,
            guest_name=guest["name"],
            guest_email=guest_email,
            podName=podName,
            episode_title=episode["title"],
            social_network=social_network,
            link=link,
            audio_url=audio_url,
        )
        return email_body
    except Exception as e:
        logger.error(f"Error rendering email template {template_path}: {str(e)}")
        return "Error loading email content."


def check_and_send_reminders():
    """Placeholder for reminder logic."""
    # Load sent emails
    sent_emails = load_sent_emails()
    # Add your reminder logic here, e.g., querying episodes/guests and sending emails
    # Example:
    # for episode in episode_repo.get_upcoming_episodes():
    #     guest = guest_repo.get_guest(episode['guest_id'])
    #     email_id = (guest['email'], episode['_id'])
    #     if email_id not in sent_emails:
    #         email_body = render_email_content('reminder', guest, episode, guest_email=guest['email'])
    #         send_email(guest['email'], "Episode Reminder", email_body)
    #         sent_emails.add(email_id)
    # Save updated sent emails
    save_sent_emails(sent_emails)
    logger.info("Checked and sent reminders.")


def load_sent_emails():
    """Loads the set of sent email identifiers from the JSON file."""
    try:
        if os.path.exists(SENT_EMAILS_FILE):
            with open(SENT_EMAILS_FILE, "r") as file:
                sent_emails_list = json.load(file)
                return set(
                    tuple(item) for item in sent_emails_list if isinstance(item, list)
                )
        else:
            logger.info(
                f"{SENT_EMAILS_FILE} not found. Starting with empty sent emails set."
            )
            return set()
    except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
        logger.error(f"Error loading {SENT_EMAILS_FILE}: {e}. Returning empty set.")
        return set()


def save_sent_emails(sent_emails_set):
    """Saves the set of sent email identifiers to the JSON file."""
    try:
        sent_emails_list = [list(item) for item in sent_emails_set]
        with open(SENT_EMAILS_FILE, "w") as file:
            json.dump(sent_emails_list, file, indent=4)
    except IOError as e:
        logger.error(f"Error saving sent emails to {SENT_EMAILS_FILE}: {e}")
    except TypeError as e:
        logger.error(f"Error serializing sent_emails data: {e}")


def check_and_send_reminders_with_context(app):
    """Wrapper to ensure Flask app context for the reminder job."""
    with app.app_context():
        check_and_send_reminders()


# --- New functions for scheduled activation invites ---

def _load_podcasts_from_xml_for_scheduler(file_path):
    """Load podcasts from an XML file for the scheduler job."""
    podcasts = []
    try:
        actual_file_path = os.path.join(os.path.dirname(__file__), '..', '..', file_path) if not os.path.isabs(file_path) else file_path
        
        if not os.path.exists(actual_file_path):
            logger.error(f"XML file for activation not found at resolved path: {actual_file_path} (original: {file_path})")
            return podcasts

        tree = ET.parse(actual_file_path)
        root = tree.getroot()
        for podcast_elem in root.findall("podcast"):
            title = podcast_elem.findtext("title")
            email_element = podcast_elem.find("emails/email")
            email = email_element.text if email_element is not None else None
            rss_feed = podcast_elem.findtext("rss")
            if title and email and rss_feed:
                podcasts.append({"title": title, "email": email, "rss_feed": rss_feed})
            else:
                logger.warning(f"Scheduler: Skipping podcast entry from XML due to missing data: Title={title}, Email={email}, RSS={rss_feed}")
        logger.info(f"Scheduler: Loaded {len(podcasts)} podcasts from {actual_file_path} for activation invites.")
    except FileNotFoundError:
        logger.error(f"Scheduler: XML file not found at {file_path}")
    except ET.ParseError:
        logger.error(f"Scheduler: Error parsing XML file at {file_path}")
    except Exception as e:
        logger.error(f"Scheduler: An unexpected error occurred while loading XML for activation: {e}", exc_info=True)
    return podcasts

def trigger_scheduled_activation_invites():
    """
    Job function to load podcasts from XML and trigger activation invites via API.
    """
    logger.info("Scheduler: Starting job to trigger activation invites.")
    podcasts_to_process = _load_podcasts_from_xml_for_scheduler(XML_FILE_PATH_FOR_ACTIVATION)
    
    if not podcasts_to_process:
        logger.info("Scheduler: No podcasts found in XML to process for activation invites.")
        return

    successful_triggers = 0
    processed_emails_in_current_run = set()  # Keep track of processed emails in this run

    for podcast_data in podcasts_to_process:
        email = podcast_data.get("email")
        rss_url = podcast_data.get("rss_feed")
        podcast_title = podcast_data.get("title")

        if not email or not rss_url or not podcast_title:
            logger.warning(f"Scheduler: Skipping entry for activation invite due to incomplete data: {podcast_data}")
            continue

        if email in processed_emails_in_current_run:
            logger.info(f"Scheduler: Skipping duplicate email in current run: {email} for podcast: {podcast_title}")
            continue

        try:
            logger.info(f"Scheduler: Processing activation invite for: {email}, Podcast: {podcast_title}")
            invite_url = f"{API_BASE_URL_FOR_ACTIVATION}/activation/invite"
            payload = {
                "email": email,
                "rss_url": rss_url,
                "podcast_title": podcast_title
            }
            response = requests.post(invite_url, json=payload, timeout=30)
            
            if response.ok:
                logger.info(f"Scheduler: Successfully triggered activation for {email}. API Response: {response.json().get('message')}")
                successful_triggers += 1
                processed_emails_in_current_run.add(email)  # Add email to processed set
            else:
                logger.error(f"Scheduler: Failed to trigger activation for {email} via API: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Scheduler: API request failed for activation invite to {email}: {req_err}", exc_info=True)
        except Exception as e:
            logger.error(f"Scheduler: Failed to process activation invite for {email}: {e}", exc_info=True)
    
    logger.info(f"Scheduler: Activation invite job finished. Successfully triggered {successful_triggers}/{len(podcasts_to_process)} invites.")

def trigger_scheduled_activation_invites_with_context(app):
    """Wrapper to ensure Flask app context for the activation invite job."""
    with app.app_context():
        trigger_scheduled_activation_invites()

# --- End new functions ---

def start_scheduler(app):
    """Initializes and starts the background scheduler."""
    # Initialize sent emails file if it doesn't exist
    if not os.path.exists(SENT_EMAILS_FILE):
        try:
            logger.info(f"Creating initial sent emails file: {SENT_EMAILS_FILE}")
            with open(SENT_EMAILS_FILE, "w") as file:
                json.dump([], file)
        except IOError as e:
            logger.error(
                f"Failed to create initial sent emails file {SENT_EMAILS_FILE}: {e}"
            )

    if not scheduler.running:
        # Add the job to run every hour, using the context wrapper
        scheduler.add_job(
            func=check_and_send_reminders_with_context,
            trigger="interval",
            hours=1,
            id="reminder_job",
            replace_existing=True,
            kwargs={"app": app},  # Pass app to the wrapper, which expects it
        )

        # Add the new job for sending activation invites (e.g., daily at 3 AM)
        scheduler.add_job(
            func=trigger_scheduled_activation_invites_with_context,
            trigger="cron",
            hour=3,
            minute=0,
            id="activation_invite_job",
            replace_existing=True,
            kwargs={"app": app}
        )

        scheduler.start()
        logger.info("⏰ Reminder scheduler started.")
        logger.info("📧 Activation invite scheduler job added.")
    else:
        logger.info("⏰ Reminder scheduler already running.")
        if not scheduler.get_job("activation_invite_job"):
            scheduler.add_job(
                func=trigger_scheduled_activation_invites_with_context,
                trigger="cron",
                hour=3,
                minute=0,
                id="activation_invite_job",
                replace_existing=True,
                kwargs={"app": app}
            )
            logger.info("📧 Activation invite scheduler job added to already running scheduler.")


def shutdown_scheduler():
    """Shuts down the scheduler gracefully."""
    if scheduler.running:
        logger.info("Shutting down reminder scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler shut down.")
    else:
        logger.info("Scheduler was not running.")


if __name__ == "__main__":
    # For testing purposes
    from flask import Flask

    app = Flask(__name__)
    logging.basicConfig(level=logging.INFO)
    start_scheduler(app)