import os
import sys
import logging
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom
from dotenv import load_dotenv
import requests  # Import requests library

# Adjust path to import from sibling directories
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
sys.path.append(os.path.join(project_root, "src"))

# --- Configuration ---
load_dotenv(os.path.join(project_root, ".env"))

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
# ------------------------------------

# --- Constants ---
XML_FILE_PATH = os.path.join(project_root, "scraped.xml")
# API_BASE_URL should point to the running Flask application
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
SEND_LINK_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/send-login-link"  # Construct endpoint URL

# --- Main Logic ---
def process_login_emails():
    if not os.path.exists(XML_FILE_PATH):
        logger.error(f"❌ XML file not found at {XML_FILE_PATH}")
        return

    try:
        tree = ET.parse(XML_FILE_PATH)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error(f"❌ Error parsing XML file {XML_FILE_PATH}: {e}")
        return

    podcasts_to_update = []
    emails_processed_count = 0
    emails_sent_successfully_count = 0  # Track successful API calls

    logger.info(
        f"🔍 Processing podcasts in {XML_FILE_PATH} to trigger login links via API endpoint: {SEND_LINK_ENDPOINT}"
    )

    session = requests.Session()  # Use a session for potential connection reuse

    for podcast_elem in root.findall("podcast"):
        sent_elem = podcast_elem.find("sent")
        email_elem = podcast_elem.find("emails/email")
        title_elem = podcast_elem.find("title")
        title = title_elem.text.strip() if title_elem is not None else "Unknown Podcast"

        if (
            sent_elem is not None
            and sent_elem.text == "false"
            and email_elem is not None
            and email_elem.text
        ):
            email = email_elem.text.strip()
            emails_processed_count += 1
            logger.info(f"SCRIPT: Processing email '{email}' for podcast '{title}'")

            try:
                # --- Call the /send-login-link endpoint ---
                logger.debug(
                    f"SCRIPT: Sending POST request to {SEND_LINK_ENDPOINT} for email: {email}"
                )
                response = session.post(
                    SEND_LINK_ENDPOINT,
                    json={"email": email},
                    headers={"Content-Type": "application/json"},
                    timeout=15,  # Add a timeout
                )
                # -----------------------------------------

                # Check response status
                if response.status_code == 200:
                    logger.info(
                        f"SCRIPT: Successfully triggered login link for {email} via API (Status: {response.status_code})"
                    )
                    emails_sent_successfully_count += 1
                    # Mark as sent in the XML tree
                    sent_elem.text = "true"
                    podcasts_to_update.append(podcast_elem)
                    time.sleep(0.5)  # Small delay between API calls
                else:
                    # Log error from API response if possible
                    error_message = "Unknown error"
                    try:
                        error_data = response.json()
                        error_message = error_data.get("error", response.text)
                    except requests.exceptions.JSONDecodeError:
                        error_message = response.text  # Use raw text if not JSON
                    logger.error(
                        f"SCRIPT: API call failed for {email} (Status: {response.status_code}): {error_message}"
                    )

            except requests.exceptions.RequestException as req_err:
                logger.error(
                    f"SCRIPT: Network error calling API for {email}: {req_err}",
                    exc_info=True,
                )
            except Exception as e:
                logger.error(
                    f"SCRIPT: Unexpected error processing email {email} for podcast '{title}': {e}",
                    exc_info=True,
                )

    # Save changes back to the XML file
    if podcasts_to_update:
        try:
            # Pretty print XML before saving
            xml_str = ET.tostring(root, encoding="unicode")
            dom = minidom.parseString(xml_str)
            pretty_xml_str = dom.toprettyxml(indent="  ")
            pretty_xml_str = os.linesep.join(
                [s for s in pretty_xml_str.splitlines() if s.strip()]
            )

            with open(XML_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(pretty_xml_str)
            logger.info(
                f"💾 Successfully updated {len(podcasts_to_update)} entries in {XML_FILE_PATH}."
            )
        # ... existing XML saving error handling ...
        except IOError as e:
            logger.error(f"❌ Error writing updated XML file: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Unexpected error saving XML: {e}", exc_info=True)

    logger.info(
        f"🏁 Finished processing. Processed {emails_processed_count} emails. Successfully triggered {emails_sent_successfully_count} login links via API."
    )


if __name__ == "__main__":
    # Ensure the Flask app is running and accessible at API_BASE_URL before running this script
    logger.info(f"--- Starting Login Link Trigger Script ---")
    logger.info(f"Target API Endpoint: {SEND_LINK_ENDPOINT}")
    process_login_emails()
    logger.info(f"--- Script Finished ---")
