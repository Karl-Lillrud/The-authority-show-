import os
import sys
import logging
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom
from dotenv import load_dotenv
from flask import Flask  # Required for context for URL generation and SECRET_KEY
from itsdangerous import URLSafeTimedSerializer

# Adjust path to import from sibling directories
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
sys.path.append(os.path.join(project_root, "src"))

from backend.utils.email_utils import (
    send_podcaster_activation_email,
)  # Assuming this will be created

# --- Configuration ---
load_dotenv(os.path.join(project_root, ".env"))  # Load .env from project root

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

XML_FILE_PATH = os.path.join(project_root, "scraped.xml")
# Use API_BASE_URL for link generation, fallback needed if running script outside Flask app context
API_BASE_URL = os.getenv(
    "API_BASE_URL", "http://127.0.0.1:8000"
)  # Default for local dev
# Need Flask app context for SECRET_KEY and url_for, create a dummy app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SERVER_NAME"] = API_BASE_URL.replace("http://", "").replace(
    "https://", ""
)  # For url_for


# --- Main Logic ---
def process_activation_emails():
    if not os.path.exists(XML_FILE_PATH):
        logger.error(f"❌ XML file not found at {XML_FILE_PATH}")
        return

    if not app.config["SECRET_KEY"]:
        logger.error(
            "❌ SECRET_KEY not set in environment variables. Cannot generate tokens."
        )
        return

    try:
        tree = ET.parse(XML_FILE_PATH)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error(f"❌ Error parsing XML file {XML_FILE_PATH}: {e}")
        return

    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    podcasts_to_update = []
    emails_sent_count = 0

    logger.info(f"🔍 Processing podcasts in {XML_FILE_PATH} for activation emails...")

    with app.app_context():  # Need app context for url_for
        for podcast_elem in root.findall("podcast"):
            sent_elem = podcast_elem.find("sent")
            email_elem = podcast_elem.find("emails/email")  # Get the first email
            rss_elem = podcast_elem.find("rssUrl")  # Look for rssUrl tag

            if (
                sent_elem is not None
                and sent_elem.text == "false"
                and email_elem is not None
                and rss_elem is not None
            ):
                email = email_elem.text.strip()
                rss_url = rss_elem.text.strip()  # Get text from rssUrl tag
                title = (
                    podcast_elem.find("title").text.strip()
                    if podcast_elem.find("title") is not None
                    else "Unknown Podcast"
                )

                if not email or not rss_url:
                    logger.warning(
                        f"⚠️ Skipping podcast '{title}' due to missing email or RSS URL."
                    )
                    continue

                logger.info(f"Processing activation for: {title} ({email})")

                try:
                    # Generate token containing email and RSS URL
                    token_data = {"email": email, "rss_url": rss_url}
                    token = serializer.dumps(
                        token_data, salt="podcaster-activation-salt"
                    )

                    # Construct activation link (points to frontend, which will call backend API)
                    # The frontend URL needs to be configured or passed as an env variable
                    frontend_base_url = os.getenv(
                        "FRONTEND_URL", API_BASE_URL
                    )  # Use API_BASE_URL as fallback
                    activation_link = f"{frontend_base_url}/activate?token={token}"  # Example frontend route

                    # Send the email
                    logger.info(
                        f"📧 Sending activation email to {email} with link: {activation_link}"
                    )
                    email_result = send_podcaster_activation_email(
                        email, activation_link
                    )

                    if email_result.get("success"):
                        logger.info(
                            f"✅ Activation email sent successfully to {email}."
                        )
                        sent_elem.text = "true"  # Mark as sent in the XML tree
                        podcasts_to_update.append(
                            podcast_elem
                        )  # Track for saving later
                        emails_sent_count += 1
                        time.sleep(1)  # Small delay between emails
                    else:
                        logger.error(
                            f"❌ Failed to send activation email to {email}: {email_result.get('error')}"
                        )

                except Exception as e:
                    logger.error(
                        f"❌ Error processing podcast '{title}' ({email}): {e}",
                        exc_info=True,
                    )

    # Save changes back to the XML file
    if podcasts_to_update:
        try:
            # Pretty print XML before saving
            xml_str = ET.tostring(root, encoding="unicode")
            dom = minidom.parseString(xml_str)
            pretty_xml_str = dom.toprettyxml(indent="  ")

            with open(XML_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(pretty_xml_str)
            logger.info(
                f"💾 Successfully updated {len(podcasts_to_update)} entries in {XML_FILE_PATH}."
            )
        except IOError as e:
            logger.error(f"❌ Error writing updated XML file: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Unexpected error saving XML: {e}", exc_info=True)

    logger.info(f"🏁 Finished processing. Sent {emails_sent_count} activation emails.")


if __name__ == "__main__":
    process_activation_emails()
