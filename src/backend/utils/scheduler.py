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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

episode_collection = database["Episodes"]
guest_collection = database["Guests"]
podcast_collection = database["Podcasts"]

SENT_EMAILS_FILE = "sent_emails.json"  
TEMPLATES_FILE = "email_templates.json" 

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

def render_email_content(trigger_name, guest, episode):
    """
    Render the email content for a given trigger, guest, and episode.
    """
    try:
        template_path = f"emails/{trigger_name}_email.html"
        email_body = render_template(
            template_path,
            guest_name=guest["name"],
            podName="The Authority Show",
            episode_title=episode["title"]
        )
        return email_body
    except Exception as e:
        logger.error(f"Error rendering email template {template_path}: {str(e)}")
        return "Error loading email content."

def check_and_send_emails():
    today = datetime.now(timezone.utc)
    sent_emails = load_sent_emails()

    triggers = {
        "booking": {"status": "Not Recorded", "time_check": None},
        "preparation": {"status": "Not Recorded", "time_check": timedelta(days=1)},
        "missing_info": {"status": "Not Recorded", "time_check": timedelta(days=20)},
        "publishing_reminder": {"status": "Recorded", "time_check": timedelta(days=7)},
        "join_link": {"status": "Not Recorded", "time_check": timedelta(hours=1)},
        "thank_you": {"status": "Published", "time_check": timedelta(days=0)},
        "recommendations": {"status": "Published", "time_check": timedelta(days=14)},
        "suggestions": {"status": "Published", "time_check": timedelta(days=0)},
        "missing_social_media": {"status": "Recorded", "time_check": None},
    }

    for trigger_name, trigger_details in triggers.items():
        logger.info(f"Processing trigger: {trigger_name}")

        required_status = trigger_details["status"]
        time_check = trigger_details["time_check"]

        query = {"status": required_status}
        if time_check is not None:
            if time_check > timedelta(0):
                query["publishDate"] = {"$gte": today, "$lte": today + time_check}
            else:
                query["publishDate"] = {"$gte": today + time_check, "$lte": today}

        if trigger_name == "missing_social_media":
            query = {"status": "Published"}

        try:
            episodes = list(episode_collection.find(query))
            logger.info(f"Found {len(episodes)} episodes for trigger '{trigger_name}'.")

            for episode in episodes:
                episode_id = str(episode["_id"])
                podcast_id = str(episode.get("podcast_id"))  # Fetch the correct podcast_id

                # Skip if the email for this trigger has already been sent
                if episode_id in sent_emails and sent_emails[episode_id]["triggers"].get(trigger_name):
                    logger.info(f"Trigger '{trigger_name}' already processed for episode {episode['title']}.")
                    continue

                guest_id = episode.get("guid")
                if not guest_id:
                    logger.warning(f"Episode {episode['title']} (ID: {episode_id}) does not have a valid 'guid'. Skipping...")
                    continue

                guest = guest_collection.find_one({"_id": guest_id})
                if not guest:
                    logger.warning(f"No valid guest found for episode {episode['title']} (Guest GUID: {guest_id}).")
                    continue

                subject = f"{trigger_name.capitalize()} Email"

                try:
                    email_body = render_email_content(trigger_name, guest, episode)
                    send_email(guest["email"], subject, email_body)
                    logger.info(f"Email sent to {guest['name']} ({guest['email']}) for trigger '{trigger_name}'.")

                    # Save the email as sent
                    if episode_id not in sent_emails:
                        sent_emails[episode_id] = {"podcastId": podcast_id, "triggers": {}}
                    sent_emails[episode_id]["triggers"][trigger_name] = True
                    save_sent_emails(sent_emails)

                except Exception as e:
                    logger.error(f"Failed to send email to {guest['name']} ({guest['email']}): {str(e)}")

        except Exception as e:
            logger.error(f"Error processing trigger '{trigger_name}': {str(e)}")

    logger.info("Finished processing all triggers.")

# scheduler.py
def start_scheduler(app):
    """Start the scheduler."""
    scheduler = BackgroundScheduler()
    # Run the check_and_send_emails function every 30 seconds
    scheduler.add_job(
        lambda: app.app_context().push() or check_and_send_emails(),
        "interval",
        seconds=30
    )
    scheduler.start()
    logger.info("Scheduler started. Running checks for emails every 30 seconds for testing.")

if __name__ == "__main__":
    from app import app 
    try:
        start_scheduler(app)  
        while True:
            time.sleep(1)  # Sleep to prevent high CPU usage
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shut down gracefully.")
