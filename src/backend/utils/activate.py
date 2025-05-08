import sys
import os
import time  # Import time for delays between batches
from flask import Flask  # Import Flask for application context
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from backend.utils.email_utils import send_activation_email, validate_email
from backend.services.rss_Service import RSSService
from backend.services.authService import AuthService
from backend.database.mongo_connection import collection

# Constants
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
XML_FILE_PATH = os.path.join(ROOT_DIR, "test.xml")  # Path to the XML file
INITIAL_EMAIL_COUNT = 30  # Start with 30 emails on the first day
INCREMENT_RATE = 0.25  # 25% daily increment
LAST_RUN_FILE = "last_run.txt"
BATCH_SIZE = 10  # Number of emails to send per batch
BATCH_DELAY = 60  # Delay between batches in seconds

# Load environment variables
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")  # Default to localhost if not set
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")  # Load SECRET_KEY from .env or use a default

# Create a Flask app instance and configure the template folder
app = Flask(__name__, template_folder="../../frontend/templates")

def get_posts_from_xml(file_path):
    """Parse the XML file and extract posts."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    posts = []
    for podcast in root.findall("podcast"):
        title = podcast.find("title").text
        rss_feed = podcast.find("rss").text
        emails = [email.text for email in podcast.find("emails").findall("email")]
        for email in emails:
            posts.append({"title": title, "email": email, "rss_feed": rss_feed})
    print(f"Loaded posts: {posts}")  # Debug log
    return posts

def has_email_been_sent(email):
    """Check if the email has already been sent."""
    # Temporarily disable the check for testing purposes
    return False

def mark_email_as_sent(email):
    """Mark the email as sent in the database."""
    collection.database.SentEmails.insert_one({"email": email, "sent_at": datetime.utcnow()})

def validate_and_send_email(post, activation_link):
    """Validate email and send activation email."""
    email = post["email"]
    if has_email_been_sent(email):
        print(f"Email already sent to {email}. Skipping.")
        return False
    if not validate_email(email):
        print(f"Invalid email: {email}")
        return False
    # Fetch artwork from RSS feed
    rss_data, status_code = RSSService().fetch_rss_feed(post["rss_feed"])
    if status_code != 200:
        print(f"Failed to fetch RSS feed for {email}")
        return False
    artwork_url = rss_data.get("imageUrl", "")
    send_activation_email(email, activation_link, post["title"], artwork_url)
    mark_email_as_sent(email)
    print(f"Activation email sent to {email}")
    return True

def calculate_emails_to_send():
    """Calculate the number of emails to send based on the last run."""
    # Override logic for testing purposes
    print("Overriding email count for testing purposes.")  # Debug log
    return 1  # Always send at least 1 email for testing

def update_last_run(email_count):
    """Update the last run file with the current date and email count."""
    with open(LAST_RUN_FILE, "w") as file:
        file.write(f"{datetime.now().strftime('%Y-%m-%d')},{email_count}")

def main():
    posts = get_posts_from_xml(XML_FILE_PATH)
    print(f"Posts loaded: {posts}")  # Debug log
    emails_to_send = calculate_emails_to_send()
    print(f"Emails to send: {emails_to_send}")  # Debug log
    sent_count = 0

    for i in range(0, len(posts), BATCH_SIZE):
        if sent_count >= emails_to_send:
            break

        batch = posts[i:i + BATCH_SIZE]
        print(f"Processing batch: {batch}")  # Debug log
        for post in batch:
            if sent_count >= emails_to_send:
                break

            # Generate activation link
            auth_service = AuthService()
            token = auth_service.generate_activation_token(post["email"], post["rss_feed"], SECRET_KEY)
            activation_link = f"{API_BASE_URL}/activate?token={token}"

            # Use Flask application context for sending emails
            with app.app_context():
                if validate_and_send_email(post, activation_link):
                    sent_count += 1

        # Delay between batches
        if i + BATCH_SIZE < len(posts):
            print(f"Batch sent. Waiting {BATCH_DELAY} seconds before sending the next batch...")
            time.sleep(BATCH_DELAY)

    update_last_run(sent_count)
    print(f"Sent {sent_count} emails today.")

if __name__ == "__main__":
    main()
