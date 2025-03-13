import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from backend.utils.guest_followup_email import send_guest_followup_email  # Use relative import
from backend.database.mongo_connection import database  # Import the database from mongo_connection
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB collections
episode_collection = database["Episodes"]
guest_collection = database["Guests"]
print("Collections:", database.list_collection_names())

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
            logger.info(f"Processing episode: {episode['title']} (ID: {episode['id']})")
            guest = guest_collection.find_one({"id": episode["guestId"]})
            if guest:
                logger.info(f"Found guest: {guest['name']} (Email: {guest.get('email', 'N/A')})")
                if "email" in guest:
                    try:
                        logger.info(f"Attempting to send follow-up email to {guest['name']} ({guest['email']})")
                        send_guest_followup_email(app, guest["email"], guest["name"])
                        logger.info(f"Follow-up email sent to {guest['name']} ({guest['email']})")
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
