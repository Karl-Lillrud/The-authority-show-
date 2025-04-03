import json
import os
import logging
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from backend.utils.email_utils import send_email  # Import send_email from email_utils.py
from backend.database.mongo_connection import database  # Import the database from mongo_connection
import time
from flask import render_template

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB collections
episode_collection = database["Episodes"]
guest_collection = database["Guests"]
podcast_collection = database["Podcasts"]

SENT_EMAILS_FILE = "sent_emails.json"  # JSON file to track sent emails
TEMPLATES_FILE = "email_templates.json"  # File with email templates

# Ensure the sent_emails.json file exists
if not os.path.exists(SENT_EMAILS_FILE):
    with open(SENT_EMAILS_FILE, "w") as file:
        json.dump({}, file)  # Initialize an empty dictionary

def load_sent_emails():
    """Load the list of sent emails (episode IDs and trigger names)."""
    try:
        with open(SENT_EMAILS_FILE, "r") as file:  # Fixed typo here
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

def parse_publish_date(publish_date):
    """Convert a publishDate to an offset-aware datetime object if it's a string."""
    if isinstance(publish_date, datetime):
        # If publish_date is naive, make it offset-aware
        if publish_date.tzinfo is None:
            return publish_date.replace(tzinfo=timezone.utc)
        return publish_date  # Already offset-aware
    try:
        # Parse the string and make it offset-aware
        return datetime.strptime(publish_date, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
    except ValueError as e:
        logger.error(f"Failed to parse publishDate '{publish_date}': {str(e)}")
        return None
    except TypeError as e:
        logger.error(f"Invalid type for publishDate: {type(publish_date)}. Error: {str(e)}")
        return None

def check_and_send_emails():
    """Check for episodes based on multiple triggers and send corresponding emails."""
    today = datetime.now(timezone.utc)
    logger.info(f"Checking for episodes based on triggers. Today: {today}")

    # Load sent emails to track which ones have already been processed
    sent_emails = load_sent_emails()

    # Define triggers with their corresponding conditions
    triggers = {
        "booking": {"status": "Not Recorded", "time_check": None},  # Send immediately
        "preparation": {"status": "Not Recorded", "time_check": timedelta(days=1)},  # 1 day before publishDate
        "missing_info": {"status": "Not Recorded", "time_check": timedelta(days=20)},  # 20 days before publishDate
        "publishing_reminder": {"status": "Recorded", "time_check": timedelta(days=7)},  # 7 days before publishDate
        "join_link": {"status": "Not Recorded", "time_check": timedelta(hours=1)},  # 1 hour before publishDate
        "thank_you": {"status": "Published", "time_check": timedelta(days=0)},  # Immediately after publishDate
        "recommendations": {"status": "Published", "time_check": timedelta(days=14)},  # 14 days after publishDate
        "suggestions": {"status": "Published", "time_check": timedelta(days=0)},  # Immediately after publishDate
        "missing_social_media": {"status": "Recorded", "time_check": None},  # Special trigger for missing social media
    }

    # Process each trigger
    for trigger_name, trigger_details in triggers.items():
        logger.info(f"Starting to process trigger: {trigger_name}")

        # Extract status and time_check for the trigger
        required_status = trigger_details["status"]
        time_check = trigger_details["time_check"]

        # Build the query
        query = {"status": required_status}
        if time_check is not None:
            if time_check > timedelta(0):  # Before publishDate
                query["publishDate"] = {"$gte": today, "$lte": today + time_check}
            else:  # After publishDate
                query["publishDate"] = {"$gte": today + time_check, "$lte": today}

        # Special logic for missing_social_media trigger
        if trigger_name == "missing_social_media":
            query = {
                "status": "Published",  # Only check for published episodes
            }

        # Log the query for debugging
        logger.info(f"Query for trigger '{trigger_name}': {query}")

        try:
            # Execute the query
            episodes = list(episode_collection.find(query))
            logger.info(f"Found {len(episodes)} episodes matching the trigger '{trigger_name}'.")

            for episode in episodes:
                episode_id = str(episode["_id"])

                # Skip if the email for this trigger has already been sent
                if episode_id in sent_emails and sent_emails[episode_id].get(trigger_name):
                    logger.info(f"Trigger '{trigger_name}' already processed for episode {episode['title']}.")
                    continue

                # Process the episode
                guest_id = episode.get("guid")
                if not guest_id:
                    logger.warning(f"Episode {episode['title']} (ID: {episode_id}) does not have a valid 'guid'. Skipping...")
                    continue

                guest = guest_collection.find_one({"_id": guest_id})
                if not guest:
                    logger.warning(f"No valid guest found for episode {episode['title']} (Guest GUID: {guest_id}).")
                    continue

                # Log the guest's social media fields
                logger.info(f"Checking social media handles for guest {guest['name']}: LinkedIn='{guest.get('linkedin')}', Twitter='{guest.get('twitter')}'")

                # Check for missing social media handles
                if not guest.get("linkedin") or guest.get("linkedin") == "" or not guest.get("twitter") or guest.get("twitter") == "":
                    # Send the email
                    try:
                        subject = "Missing Social Media Information"
                        template_path = "emails/missing_social_media_email.html"
                        email_body = render_template(
                            template_path,
                            guest_name=guest["name"],
                            social_network="LinkedIn or Twitter",
                            podName="The Authority Show"
                        )
                        send_email(guest["email"], subject, email_body)
                        logger.info(f"Email sent to {guest['name']} ({guest['email']}) for trigger '{trigger_name}'.")

                        # Mark the trigger as processed
                        if episode_id not in sent_emails:
                            sent_emails[episode_id] = {}
                        sent_emails[episode_id][trigger_name] = True
                        save_sent_emails(sent_emails)

                    except Exception as e:
                        logger.error(f"Failed to send email to {guest['name']} ({guest['email']}): {str(e)}")
                else:
                    logger.info(f"Guest {guest['name']} has all required social media handles. Skipping...")

        except Exception as e:
            logger.error(f"Error processing trigger '{trigger_name}': {str(e)}")

    logger.info("Finished processing all triggers.")

# scheduler.py
def start_scheduler(app):
    """Start the scheduler."""
    scheduler = BackgroundScheduler()

    # Wrap the job in app.app_context()
    scheduler.add_job(lambda: app.app_context().push() or check_and_send_emails(), "interval", seconds=30)
    scheduler.start()
    logger.info("Scheduler started. Running checks for emails every minute.")

if __name__ == "__main__":
    from app import app  # Import the Flask app
    try:
        start_scheduler(app)  # Pass the app to the scheduler
        while True:
            time.sleep(1)  # Sleep to prevent high CPU usage
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shut down gracefully.")
