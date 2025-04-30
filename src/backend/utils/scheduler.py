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

logger = logging.getLogger(__name__)

# Define the path for the sent emails file (Consider a more robust location)
# Using os.path.join for better path construction
SENT_EMAILS_FILE = os.path.join(os.path.dirname(__file__), "sent_emails.json")

scheduler = BackgroundScheduler(daemon=True)
guest_repo = GuestRepository()
episode_repo = EpisodeRepository()

def render_email_content(trigger_name, guest, episode, social_network=None, guest_email=None, podName=None, link=None, audio_url=None):
    try:
        template_path = f"emails/{trigger_name}_email.html"
        email_body = render_template(
            template_path,
            guest_name=guest["name"],  # Dynamically inject guest name
            guest_email=guest_email,  # Dynamically inject guest email
            podName=podName,  # Dynamically inject podcast name
            episode_title=episode["title"],  # Dynamically inject episode title
            social_network=social_network,  # Dynamically inject missing social networks
            link=link,  # Dynamically inject episode link
            audio_url=audio_url  # Dynamically inject audio URL
        )
        return email_body
    except Exception as e:
        logger.error(f"Error rendering email template {template_path}: {str(e)}")
        return "Error loading email content."

def check_and_send_reminders():
    # ... existing reminder logic ...
    # Make sure 'sent_emails' is loaded or accessible here
    # Load sent_emails inside the function or pass it as an argument if needed
    # For simplicity, let's load it here, assuming it's initialized in start_scheduler
    sent_emails = load_sent_emails()
    # ... rest of the reminder logic using sent_emails ...
    # Remember to save the updated set back to the file
    save_sent_emails(sent_emails)


def load_sent_emails():
    """Loads the set of sent email identifiers from the JSON file."""
    try:
        if os.path.exists(SENT_EMAILS_FILE):
            with open(SENT_EMAILS_FILE, "r") as file:
                sent_emails_list = json.load(file)
                # Ensure items are tuples for hashing in a set
                return set(tuple(item) for item in sent_emails_list if isinstance(item, list))
        else:
            # If file doesn't exist, return empty set (it will be created on save)
            logger.info(f"{SENT_EMAILS_FILE} not found. Starting with empty sent emails set.")
            return set()
    except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
        logger.error(f"Error loading {SENT_EMAILS_FILE}: {e}. Returning empty set.")
        return set()

def save_sent_emails(sent_emails_set):
    """Saves the set of sent email identifiers to the JSON file."""
    try:
        # Convert set of tuples back to list of lists for JSON serialization
        sent_emails_list = [list(item) for item in sent_emails_set]
        with open(SENT_EMAILS_FILE, "w") as file:
            json.dump(sent_emails_list, file, indent=4) # Add indent for readability
    except IOError as e:
        logger.error(f"Error saving sent emails to {SENT_EMAILS_FILE}: {e}")
    except TypeError as e:
        logger.error(f"Error serializing sent_emails data: {e}")


def start_scheduler(app):
    """Initializes and starts the background scheduler."""
    if not os.path.exists(SENT_EMAILS_FILE):
        try:
            logger.info(f"Creating initial sent emails file: {SENT_EMAILS_FILE}")
            with open(SENT_EMAILS_FILE, "w") as file:
                json.dump([], file)
        except IOError as e:
            logger.error(f"Failed to create initial sent emails file {SENT_EMAILS_FILE}: {e}")
            return

    if not scheduler.running:
        scheduler.add_job(
            func=check_and_send_reminders_with_context,  # ✅ Explicitly define func
            trigger="interval",
            hours=1,
            id="reminder_job",
            replace_existing=True,
            args=[app]  # ✅ This works now
        )
        scheduler.start()
        logger.info("⏰ Reminder scheduler started.")
    else:
        logger.info("⏰ Reminder scheduler already running.")


# Ensure the app context is available within the scheduled job if needed
def check_and_send_reminders_with_context(app):
     with app.app_context():
         check_and_send_reminders()

# Modify the job definition in start_scheduler to use the context wrapper
# scheduler.add_job(
#     check_and_send_reminders_with_context,
#     trigger="interval",
#     hours=1,
#     id="reminder_job",
#     replace_existing=True,
#     kwargs={'app': app}
# )
