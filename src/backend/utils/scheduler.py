import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

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
episode_collection = database["episodes"]
guest_collection = database["guests"]

def check_and_send_followups():
    """Check for episodes published 14 days ago and send follow-up emails."""
    fourteen_days_ago = datetime.now(timezone.utc) - timedelta(days=14)
    logger.info(f"Checking for episodes published on or before: {fourteen_days_ago}")
    
    query = {
        "publishDate": {"$lte": fourteen_days_ago},
        "status": "Published"
    }
    logger.info(f"Query: {query}")
    
    episodes = episode_collection.find(query)
    episode_count = episode_collection.count_documents(query)
    
    logger.info(f"Found {episode_count} episodes published 14 days ago or earlier.")
    
    for episode in episodes:
        logger.info(f"Processing episode: {episode['title']} (ID: {episode['id']})")
        guest = guest_collection.find_one({"id": episode["guestId"]})
        if guest:
            logger.info(f"Found guest: {guest['name']} (Email: {guest.get('email', 'N/A')})")
            if "email" in guest:
                try:
                    send_guest_followup_email(guest["email"], guest["name"])
                    logger.info(f"Follow-up email sent to {guest['name']} ({guest['email']})")
                except Exception as e:
                    logger.error(f"Failed to send follow-up email to {guest['name']} ({guest['email']}): {str(e)}")
            else:
                logger.warning(f"Guest {guest['name']} does not have an email address.")
        else:
            logger.warning(f"Guest not found for episode: {episode['title']} (Guest ID: {episode['guestId']})")

def start_scheduler():
    """Start the scheduler."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_send_followups, "interval", minutes=1)
    scheduler.start()
    logger.info("Scheduler started. Running checks for follow-up emails every minute.")

if __name__ == "__main__":
    scheduler = start_scheduler()
    try:
        while True:
            time.sleep(1)   # Sleep to prevent high CPU usage
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler shut down gracefully.")
