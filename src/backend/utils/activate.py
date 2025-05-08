import os
import xml.etree.ElementTree as ET
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip('/')
XML_FILE_PATH = os.getenv("ACTIVATION_XML_FILE_PATH", "../test.xml")

def load_podcasts_from_xml(file_path):
    """Load podcasts from an XML file."""
    podcasts = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for podcast_elem in root.findall("podcast"):
            title = podcast_elem.findtext("title")
            email_element = podcast_elem.find("emails/email")
            email = email_element.text if email_element is not None else None
            rss_feed = podcast_elem.findtext("rss")
            if title and email and rss_feed:
                podcasts.append({"title": title, "email": email, "rss_feed": rss_feed})
            else:
                logger.warning(f"Skipping podcast entry due to missing data: Title={title}, Email={email}, RSS={rss_feed}")
        logger.info(f"Loaded {len(podcasts)} podcasts from {file_path}")
    except FileNotFoundError:
        logger.error(f"XML file not found at {file_path}")
    except ET.ParseError:
        logger.error(f"Error parsing XML file at {file_path}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading XML: {e}", exc_info=True)
    return podcasts

def main():
    logger.info("Starting activation script (API mode)...")
    podcasts_to_process = load_podcasts_from_xml(XML_FILE_PATH)
    if not podcasts_to_process:
        logger.info("No podcasts to process. Exiting.")
        return

    emails_sent_successfully = 0
    total_processed = 0

    for podcast_data in podcasts_to_process:
        total_processed += 1
        email = podcast_data.get("email")
        rss_url = podcast_data.get("rss_feed")
        podcast_title = podcast_data.get("title")

        if not email or not rss_url or not podcast_title:
            logger.warning(f"Skipping entry due to incomplete data: {podcast_data}")
            continue

        try:
            logger.info(f"Processing activation for: {email}, Podcast: {podcast_title}, RSS: {rss_url}")

            invite_url = f"{API_BASE_URL}/activation/invite"
            payload = {
                "email": email,
                "rss_url": rss_url,
                "podcast_title": podcast_title
            }
            response = requests.post(invite_url, json=payload)
            
            if response.ok:
                response_data = response.json()
                activation_link = response_data.get("activation_link")
                if activation_link:
                    logger.info(f"Constructed activation link for {email}: {activation_link}")
                else:
                    logger.warning(f"Activation link not found in API response for {email}")
                
                logger.info(f"Successfully triggered activation for {email}. API Message: {response_data.get('message')}")
                emails_sent_successfully += 1
            else:
                logger.error(f"Failed to trigger activation for {email}: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as req_err:
            logger.error(f"API request failed for {email}: {req_err}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to process activation for {email}: {e}", exc_info=True)

    logger.info(f"Activation script finished. Processed {total_processed} entries. Successfully triggered {emails_sent_successfully} activations.")

if __name__ == "__main__":
    main()
