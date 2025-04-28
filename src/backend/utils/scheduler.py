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
from backend.utils.trigger_config import TRIGGERS  # Import the triggers configuration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

episode_collection = database["Episodes"]
guest_collection = database["Guests"]
podcast_collection = database["Podcasts"]

# Define the new paths
BASE_JSON_PATH = os.path.join(os.path.dirname(__file__), "../../Frontend/static/json")
SENT_EMAILS_FILE = os.path.join(BASE_JSON_PATH, "sent_emails.json")
TEMPLATES_FILE = os.path.join(BASE_JSON_PATH, "email_templates.json")
CUSTOM_TRIGGERS_FILE = os.path.join(BASE_JSON_PATH, "custom_triggers.json")

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

def load_custom_triggers():
    """Load custom triggers for podcasts."""
    try:
        with open(CUSTOM_TRIGGERS_FILE, "r") as file:
            custom_triggers = json.load(file)

        # Convert time_check back to timedelta
        for podcast_id, triggers in custom_triggers.items():
            for trigger_name, trigger_details in triggers.items():
                if trigger_details["time_check"] is not None:
                    trigger_details["time_check"] = timedelta(seconds=trigger_details["time_check"])

        return custom_triggers
    except Exception as e:
        logger.error(f"Error loading custom triggers file: {str(e)}")
        return {}

def check_and_send_emails():
    today = datetime.now(timezone.utc)
    sent_emails = load_sent_emails()
    custom_triggers = load_custom_triggers()

    # Step 1: Process custom triggers
    for podcast_id, podcast_triggers in custom_triggers.items():
        logger.info(f"Processing custom triggers for podcast: {podcast_id}")

        # Fetch all episodes for the podcast
        episodes = list(episode_collection.find({"podcast_id": podcast_id}))
        for episode in episodes:
            episode_id = str(episode["_id"])

            for trigger_name, trigger_details in podcast_triggers.items():
                required_status = trigger_details["status"]
                time_check = trigger_details["time_check"]  # Already a timedelta object

                # Check if the episode matches the custom trigger
                if episode["status"] == required_status and "publishDate" in episode:
                    publish_date = parse_publish_date(episode["publishDate"])
                    if publish_date and today - timedelta(days=1) <= publish_date <= today + time_check:
                        # Skip if the email has already been sent
                        if episode_id in sent_emails and sent_emails[episode_id]["triggers"].get(trigger_name):
                            logger.info(f"Custom trigger '{trigger_name}' already processed for episode {episode['title']}.")
                            continue

                        # Send the email
                        guest = guest_collection.find_one({"_id": episode["guid"]})
                        if not guest:
                            logger.warning(f"No valid guest found for episode {episode['title']} (Guest GUID: {episode['guid']}).")
                            continue

                        link = episode.get("link", "#")
                        audio_url = episode.get("audioUrl", "#")
                        subject = f"{trigger_name.replace('_', ' ').title()} Email"

                        email_body = render_email_content(
                            trigger_name,
                            guest,
                            episode,
                            guest_email=guest["email"],
                            podName="The Authority Show",
                            link=link,
                            audio_url=audio_url
                        )
                        send_email(guest["email"], subject, email_body)
                        logger.info(f"Email sent to {guest['name']} ({guest['email']}) for custom trigger '{trigger_name}'.")

                        # Mark the email as sent
                        if episode_id not in sent_emails:
                            sent_emails[episode_id] = {"podcastId": podcast_id, "triggers": {}}
                        sent_emails[episode_id]["triggers"][trigger_name] = True
                        save_sent_emails(sent_emails)

    # Step 2: Process normal triggers
    for trigger_name, trigger_details in TRIGGERS.items():  # Use imported TRIGGERS
        logger.info(f"Processing normal trigger: {trigger_name}")

        required_status = trigger_details["status"]
        time_check = trigger_details["time_check"]

        query = {"status": required_status}
        if time_check is not None:
            query["publishDate"] = {
                "$gte": today - timedelta(days=1),  # 24 hours before now
                "$lte": today + time_check  # Up to the specified time_check
            }

        try:
            episodes = list(episode_collection.find(query))
            for episode in episodes:
                episode_id = str(episode["_id"])
                podcast_id = str(episode.get("podcast_id"))

                # Skip if the email has already been sent
                if episode_id in sent_emails and sent_emails[episode_id]["triggers"].get(trigger_name):
                    logger.info(f"Trigger '{trigger_name}' already processed for episode {episode['title']}.")
                    continue

                # Skip if a custom trigger exists for this podcast and trigger
                if custom_triggers.get(podcast_id, {}).get(trigger_name):
                    logger.info(f"Custom trigger exists for '{trigger_name}' on podcast {podcast_id}. Skipping normal trigger.")
                    continue

                # Send the email
                guest = guest_collection.find_one({"_id": episode["guid"]})
                if not guest:
                    logger.warning(f"No valid guest found for episode {episode['title']} (Guest GUID: {episode['guid']}).")
                    continue

                link = episode.get("link", "#")
                audio_url = episode.get("audioUrl", "#")
                subject = f"{trigger_name.replace('_', ' ').title()} Email"

                email_body = render_email_content(
                    trigger_name,
                    guest,
                    episode,
                    guest_email=guest["email"],
                    podName="The Authority Show",
                    link=link,
                    audio_url=audio_url
                )
                send_email(guest["email"], subject, email_body)
                logger.info(f"Email sent to {guest['name']} ({guest['email']}) for trigger '{trigger_name}'.")

                # Mark the email as sent
                if episode_id not in sent_emails:
                    sent_emails[episode_id] = {"podcastId": podcast_id, "triggers": {}}
                sent_emails[episode_id]["triggers"][trigger_name] = True
                save_sent_emails(sent_emails)

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
