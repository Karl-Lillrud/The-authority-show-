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

# Define the path for the sent emails file
SENT_EMAILS_FILE = os.path.join(os.path.dirname(__file__), "sent_emails.json")

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
        scheduler.start()
        logger.info("⏰ Reminder scheduler started.")
    else:
        logger.info("⏰ Reminder scheduler already running.")


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