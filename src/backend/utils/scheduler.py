import json
import os
import logging
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from backend.utils.email_utils import send_email  # Import send_email from email_utils.py
from backend.database.mongo_connection import database  # Import the database from mongo_connection
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB collections
episode_collection = database["Episodes"]
guest_collection = database["Guests"]

SENT_EMAILS_FILE = "sent_emails.json"  # JSON file to track sent emails
TEMPLATES_FILE = "email_templates.json"  # File with email templates

# Ensure the sent_emails.json file exists
if not os.path.exists(SENT_EMAILS_FILE):
    with open(SENT_EMAILS_FILE, "w") as file:
        json.dump({}, file)  # Initialize an empty dictionary

def load_sent_emails():
    """Load the list of sent emails (episode IDs and trigger names)."""
    try:
        with open(SENT_EMAILS_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading sent emails file: {str(e)}")
        return {}

def save_sent_emails(sent_emails):
    """Save the list of sent emails (episode IDs and trigger names)."""
    try:
        with open(SENT_EMAILS_FILE, "w") as file:
            json.dump(sent_emails, file)
    except Exception as e:
        logging.error(f"Error saving sent emails file: {str(e)}")

def load_email_templates():
    """Load the email templates from the JSON file."""
    try:
        with open(TEMPLATES_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading email templates: {str(e)}")
        return {}

def log_all_episodes():
    """Log all episodes in the database."""
    all_episodes = list(episode_collection.find())
    logger.info(f"Total episodes in the database: {len(all_episodes)}")
    for episode in all_episodes:
        logger.info(f"Episode: {episode['title']} (ID: {episode['_id']}, publishDate: {episode['publishDate']}, status: {episode['status']})")

def check_and_send_emails(app):
    """Check for episodes based on multiple triggers and send corresponding emails."""
    today = datetime.now(timezone.utc)
    logger.info(f"Checking for episodes based on triggers. Today: {today}")

    # Load sent emails to track which ones have already been processed
    sent_emails = load_sent_emails()

    # Load email templates
    templates = load_email_templates()  # Load the templates here

    if not templates:
        logger.error("Email templates could not be loaded. Aborting email checks.")
        return

    # List of triggers with their corresponding email templates
    triggers = {
        "booking": "createdAt",  # 0 days after creation
        "preparation": "publishDate-14",  # 14 days before publish date
        "missing_info": "publishDate-20",  # 20 days before publish date
        "publishing_reminder": "publishDate-7",  # 7 days before publish date
        "join_link": "publishDate-1hour",  # 1 hour before publish date
        "thank_you": "publishDate+1",  # 1 day after publish date
    }

    # Process each episode
    for trigger_name, trigger_value in triggers.items():
        logger.info(f"Checking trigger: {trigger_name}")

        # Define the time offsets for different triggers
        if trigger_value == "createdAt":
            trigger_time = timedelta(days=0)  # Trigger immediately after creation
        elif trigger_value == "publishDate-14":
            trigger_time = timedelta(days=14)  # 14 days before publish date
        elif trigger_value == "publishDate-20":
            trigger_time = timedelta(days=20)  # 20 days before publish date
        elif trigger_value == "publishDate-7":
            trigger_time = timedelta(days=7)  # 7 days before publish date
        elif trigger_value == "publishDate-1hour":
            trigger_time = timedelta(hours=1)  # 1 hour before publish date
        elif trigger_value == "publishDate+1":
            trigger_time = timedelta(days=-1)  # 1 day after publish date

        # Query to find episodes based on trigger condition
        query = {}
        if trigger_name in ["preparation", "missing_info", "publishing_reminder"]:
            # Episodes published 14, 20, or 7 days ago
            query = {
                "publishDate": {"$lte": today - trigger_time},
                "status": "Published"
            }
        elif trigger_name == "join_link":
            # Episodes with 1 hour left for publishing
            query = {
                "publishDate": {"$lte": today + timedelta(hours=1)},
                "status": "Published"
            }
        elif trigger_name == "thank_you":
            # Episodes published 1 day ago
            query = {
                "publishDate": {"$lte": today - timedelta(days=-1)},
                "status": "Published"
            }

        try:
            # Execute the query
            episodes = list(episode_collection.find(query))
            episode_count = len(episodes)
            logger.info(f"Found {episode_count} episodes matching the trigger '{trigger_name}'.")

            if episode_count == 0:
                logger.info(f"No episodes found for trigger '{trigger_name}'.")

            # Log the first 5 episodes for clarity
            for episode in episodes[:5]:  # Limiting the log to first 5 episodes
                logger.info(f"Episode found: {episode['title']} (ID: {episode['_id']}, Publish Date: {episode['publishDate']})")

        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            return

        # Process each episode
        for episode in episodes:
            episode_id = str(episode["_id"])  # Convert episode ID to string for consistency

            # Initialize triggers for this episode if not present in sent_emails
            if episode_id not in sent_emails:
                sent_emails[episode_id] = {"triggers": {}}  # Initialize if episode does not exist in the file

            # Check if the trigger for this episode has already been processed
            if trigger_name in sent_emails[episode_id]["triggers"] and sent_emails[episode_id]["triggers"][trigger_name]:
                logger.info(f"Trigger '{trigger_name}' already processed for episode {episode['title']}")
                continue

            logger.info(f"Processing episode: {episode['title']} (ID: {episode_id})")
            guest_id = episode.get("guestId")  # Use .get() to avoid KeyError if 'guestId' is missing
            logger.info(f"Guest ID: {guest_id} for episode: {episode['title']}")

            if guest_id:
                guest = guest_collection.find_one({"id": guest_id})  # Corrected to use the 'id' field

                if guest:
                    logger.info(f"Found guest: {guest['name']} (Email: {guest.get('email', 'N/A')})")
                    if "email" in guest:
                        try:
                            logger.info(f"Attempting to send email to {guest['name']} ({guest['email']})")
                            # Send the email using the send_email function from email_utils.py
                            subject = templates[trigger_name]["subject"]
                            template_path = templates[trigger_name]["template"]
                            send_email(guest["email"], subject, f"This is a reminder email regarding the episode: {episode['title']} - Trigger: {trigger_name}")
                            logger.info(f"Email sent to {guest['name']} ({guest['email']})")

                            # Mark the trigger as processed for this episode
                            sent_emails[episode_id]["triggers"][trigger_name] = True
                            save_sent_emails(sent_emails)  # Save the updated list

                        except Exception as e:
                            logger.error(f"Failed to send email to {guest['name']} ({guest['email']}): {str(e)}")
                    else:
                        logger.warning(f"Guest {guest['name']} does not have an email address.")
                else:
                    logger.warning(f"Guest not found for episode: {episode['title']} (Guest ID: {guest_id})")
            else:
                logger.warning(f"Episode {episode['title']} (ID: {episode_id}) does not have a 'guestId'. Skipping...")



# scheduler.py
def start_scheduler(app):
    """Start the scheduler."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: check_and_send_emails(app), "interval", minutes=1)  # Use lambda to pass app
    scheduler.start()
    logger.info("Scheduler started. Running checks for emails every minute.")


if __name__ == "__main__":
    try:
        start_scheduler()  # Start the scheduler
        while True:
            time.sleep(1)  # Sleep to prevent high CPU usage
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shut down gracefully.")
