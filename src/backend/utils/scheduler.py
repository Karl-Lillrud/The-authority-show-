import json
import os
import logging
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from backend.services.guest_followup_email import send_guest_followup_email  # Use relative import
from backend.database.mongo_connection import database  # Import the database from mongo_connection
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB collections
episode_collection = database["Episodes"]
guest_collection = database["Guests"]

SENT_EMAILS_FILE = "sent_emails.json"  # JSON file to track sent emails

# Ensure the sent_emails.json file exists
if not os.path.exists(SENT_EMAILS_FILE):
    with open(SENT_EMAILS_FILE, "w") as file:
        json.dump({}, file)  # Initialize an empty dictionary

def load_sent_emails():
    """Load the list of sent emails (episode IDs)."""
    try:
        with open(SENT_EMAILS_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading sent emails file: {str(e)}")
        return {}

def save_sent_emails(sent_emails):
    """Save the list of sent emails (episode IDs)."""
    try:
        with open(SENT_EMAILS_FILE, "w") as file:
            json.dump(sent_emails, file)
    except Exception as e:
        logging.error(f"Error saving sent emails file: {str(e)}")

def log_all_episodes():
    """Log all episodes in the database."""
    all_episodes = list(episode_collection.find())
    logger.info(f"Total episodes in the database: {len(all_episodes)}")
    for episode in all_episodes:
        logger.info(f"Episode: {episode['title']} (ID: {episode['id']}, publishDate: {episode['publishDate']}, status: {episode['status']})")

def check_and_send_followups(app):
    """Check for episodes published 14 days ago and send follow-up emails."""
    fourteen_days_ago = datetime.now(timezone.utc) - timedelta(days=14)
    logger.info(f"Checking for episodes published on or before: {fourteen_days_ago}")

    # Load sent emails to track which ones have already been processed
    sent_emails = load_sent_emails()

    # Create query to find episodes published 14 days ago or earlier
    query = {
        "publishDate": {"$lte": fourteen_days_ago},
        "status": "Published"
    }
    logger.info(f"Query: {query}")

    try:
        # Execute the query
        episodes = list(episode_collection.find(query))
        episode_count = len(episodes)
        logger.info(f"Found {episode_count} episodes published 14 days ago or earlier.")

        if episode_count == 0:
            logger.info("No episodes found that are 14 days or older with status 'Published'.")
        
        # Log the first 5 episodes for clarity
        for episode in episodes[:5]:  # Limiting the log to first 5 episodes
            logger.info(f"Episode found: {episode['title']} (ID: {episode['id']}, Publish Date: {episode['publishDate']})")

    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return

    # Log all episodes after the query is executed
    log_all_episodes()

    # Process each episode
    with app.app_context():  # Ensure you're within the Flask app context
        for episode in episodes:
            episode_id = str(episode["id"])  # Convert episode ID to string for consistency

            # Skip this episode if its ID is already in the sent_emails file
            if episode_id in sent_emails:
                logger.info(f"Episode {episode['title']} (ID: {episode_id}) has already had a follow-up email sent.")
                continue

            logger.info(f"Processing episode: {episode['title']} (ID: {episode_id})")
            guest = guest_collection.find_one({"id": episode["guestId"]})
            if guest:
                logger.info(f"Found guest: {guest['name']} (Email: {guest.get('email', 'N/A')})")
                if "email" in guest:
                    try:
                        logger.info(f"Attempting to send follow-up email to {guest['name']} ({guest['email']})")
                        send_guest_followup_email(app, guest["email"], guest["name"])
                        logger.info(f"Follow-up email sent to {guest['name']} ({guest['email']})")

                        # Mark this episode as having had a follow-up email sent
                        sent_emails[episode_id] = True
                        save_sent_emails(sent_emails)  # Save the updated list

                    except Exception as e:
                        logger.error(f"Failed to send follow-up email to {guest['name']} ({guest['email']}): {str(e)}")
                else:
                    logger.warning(f"Guest {guest['name']} does not have an email address.")
            else:
                logger.warning(f"Guest not found for episode: {episode['title']} (Guest ID: {episode['guestId']})")

def start_scheduler(app):
    """Start the scheduler."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: check_and_send_followups(app), "interval", minutes=1)
    scheduler.start()
    logger.info("Scheduler started. Running checks for follow-up emails every minute.")

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    scheduler = start_scheduler(app)
    try:
        while True:
            time.sleep(1)   # Sleep to prevent high CPU usage
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler shut down gracefully.")
