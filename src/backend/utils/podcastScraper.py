import re
import os
import sys
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sqlite3  # Import sqlite3
import tempfile  # Import tempfile
import logging  # Import logging
# Import the download function from blob_storage
from blob_storage import download_blob_to_tempfile

load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
AZURE_DB_CONTAINER = "podmanagerfiles"
AZURE_DB_BLOB_PATH = "scrapeDb/podcastindex_feeds.db"

# Standardized Keys
KEY_TITLE = "title"
KEY_URL = "url"  # Use 'url' consistently for the link/feed URL
KEY_PUBLISHER = "publisher"
KEY_EMAILS = "emails"

# Regex for finding potential emails in text (broader, no word boundaries)
EMAIL_FIND_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
# Regex for validating a string is a complete, valid email (stricter)
EMAIL_VALIDATE_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
# Regex for extracting a valid email prefix from a string (stricter start, no end anchor)
EMAIL_EXTRACT_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# 🔑 Spotify API Credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# 🎵 Authenticate using Spotify OAuth
try:
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-read-email",
            open_browser=True
        )
    )
    sp.current_user()
    logger.info("✅ Successfully authenticated with Spotify.")
except Exception as e:
    logger.error(f"❌ Spotify Authentication Failed: {e}")
    sys.exit(1)

# 🔍 Function to Fetch Podcasts (Bypassing API Limit)
def fetch_spotify_podcasts(target_count=10):
    search_queries = [
        "podcast",
        "news podcast",
        "music podcast",
        "tech podcast",
        "sports podcast",
        "health podcast",
    ]
    podcasts = set()
    limit = 50
    max_offset = 1000

    logger.info(f"🎯 Fetching a maximum of {target_count} unique podcasts for testing.")

    for query in search_queries:
        offset = 0
        logger.info(f"Searching for podcasts with query: '{query}'")

        while offset < max_offset:
            if len(podcasts) >= target_count:
                logger.info(f"🏁 Target of {target_count} podcasts reached. Stopping search for '{query}'.")
                break

            try:
                results = sp.search(q=query, type="show", limit=limit, offset=offset)
            except Exception as api_err:
                logger.error(f"⚠️ Spotify API error during search for '{query}' at offset {offset}: {api_err}")
                break

            if not results or "shows" not in results or "items" not in results["shows"]:
                logger.info(f"ℹ️ No more results found for '{query}'.")
                break

            items = results["shows"]["items"]
            if not items:
                logger.info(f"ℹ️ No items returned for '{query}' at offset {offset}.")
                break

            initial_count = len(podcasts)
            for item in items:
                podcast_entry = (
                    item["name"],
                    item["external_urls"]["spotify"],
                    item.get("publisher", ""),
                )
                podcasts.add(podcast_entry)

                if len(podcasts) >= target_count:
                    logger.info(f"🏁 Target of {target_count} podcasts reached.")
                    break

            newly_added = len(podcasts) - initial_count
            logger.info(f"Fetched {newly_added} new unique podcasts from this batch. Total unique: {len(podcasts)}")

            if len(podcasts) >= target_count:
                break

            offset += limit

        if len(podcasts) >= target_count:
            logger.info(f"🏁 Target of {target_count} podcasts reached. Stopping all searches.")
            break

    podcast_list = [{KEY_TITLE: p[0], KEY_URL: p[1], KEY_PUBLISHER: p[2]} for p in podcasts]
    return podcast_list[:target_count]

# 📧 Function to Extract Emails and Title from a Webpage
def extract_info_from_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string.strip() if soup.title else "No title found"
            
            # Find potential emails using the broader pattern (no word boundaries)
            potential_emails = re.findall(EMAIL_FIND_PATTERN, soup.get_text())
            logger.debug(f"Found potential email candidates: {potential_emails}")
            
            cleaned_emails = set()
            for candidate in potential_emails:
                candidate = candidate.strip()  # Ensure no leading/trailing whitespace
                # Attempt to extract a valid email prefix
                match = EMAIL_EXTRACT_PATTERN.match(candidate)
                if match:
                    extracted_email = match.group(0)
                    # Validate the extracted part strictly
                    if EMAIL_VALIDATE_PATTERN.match(extracted_email):
                        cleaned_emails.add(extracted_email)
                        if extracted_email != candidate:
                            logger.info(f"Successfully extracted and validated email '{extracted_email}' from candidate '{candidate}'")
                        else:
                            logger.debug(f"Validated email directly (via extraction match): {extracted_email}")
                    else:
                        logger.warning(f"Extracted prefix '{extracted_email}' from '{candidate}' failed strict validation.")
                else:
                    logger.debug(f"Could not extract a valid email prefix from candidate: {candidate}")

            valid_emails = list(cleaned_emails)

            if valid_emails:
                logger.info(f"Found and cleaned/validated emails: {valid_emails}")
            else:
                logger.info("No valid emails found or extracted on page.")
            return {KEY_TITLE: title, KEY_EMAILS: valid_emails}
        else:
            logger.error(f"Failed to fetch {url}, status code: {response.status_code}")
            return {KEY_TITLE: "No title found", KEY_EMAILS: []}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return {KEY_TITLE: "No title found", KEY_EMAILS: []}

# 💾 Function to Fetch Data from Azure SQLite DB
def fetch_data_from_azure_db(container_name, blob_path):
    logger.info(f"Attempting to process database from Azure Blob: {container_name}/{blob_path}")
    db_podcasts = []
    temp_db_path = None

    try:
        temp_db_path = download_blob_to_tempfile(container_name, blob_path)

        if not temp_db_path:
            logger.error("Failed to download database file from Azure.")
            return db_podcasts

        conn = None
        try:
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            logger.info(f"Connected to temporary SQLite database: {temp_db_path}")

            query = "SELECT title, url, author, ownerEmail FROM feeds WHERE ownerEmail IS NOT NULL AND ownerEmail != ''"
            logger.info(f"Executing query: {query}")
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info(f"Found {len(rows)} potential podcasts in the database.")

            for row in rows:
                title, feed_url, publisher, email_str = row
                if title and feed_url and email_str:
                    cleaned_email_str = email_str.strip()
                    final_email = None
                    
                    # Attempt to extract a valid email prefix
                    match = EMAIL_EXTRACT_PATTERN.match(cleaned_email_str)
                    if match:
                        extracted_email = match.group(0)
                        # Validate the extracted part strictly
                        if EMAIL_VALIDATE_PATTERN.match(extracted_email):
                            final_email = extracted_email
                            if extracted_email != cleaned_email_str:
                                logger.info(f"Successfully extracted and validated email '{final_email}' from DB email '{email_str}'")
                            else:
                                logger.debug(f"Validated DB email directly (via extraction match): {final_email}")
                        else:
                            logger.warning(f"Extracted prefix '{extracted_email}' from DB email '{email_str}' failed strict validation.")
                    else:
                        logger.debug(f"Could not extract a valid email prefix from DB email: {email_str}")

                    if final_email:
                        db_podcasts.append({
                            KEY_TITLE: title.strip(),
                            KEY_URL: feed_url.strip(),
                            KEY_PUBLISHER: publisher.strip() if publisher else "",
                            KEY_EMAILS: [final_email]
                        })
                    else:
                        logger.warning(f"Skipping DB entry '{title}' - could not validate or clean email found in DB: '{email_str}'")
                else:
                    logger.warning(f"Skipping DB entry due to missing title, url (feed), or email: {row}")

        except sqlite3.Error as db_err:
            logger.error(f"Database error processing {temp_db_path}: {db_err}", exc_info=True)
        finally:
            if conn:
                conn.close()
                logger.info("Closed database connection.")

    except Exception as e:
        logger.error(f"An unexpected error occurred during DB processing: {e}", exc_info=True)
    finally:
        if temp_db_path and os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
                logger.info(f"Removed temporary database file: {temp_db_path}")
            except OSError as remove_err:
                logger.error(f"Error removing temporary file {temp_db_path}: {remove_err}")

    logger.info(f"Returning {len(db_podcasts)} podcasts processed from the database.")
    return db_podcasts

# 🚀 Main Execution
if __name__ == "__main__":
    logger.info("Fetching Spotify podcasts (Test Mode - Max 10)...")
    spotify_podcasts_raw = fetch_spotify_podcasts(target_count=10)
    logger.info(f"Total unique podcasts fetched from Spotify: {len(spotify_podcasts_raw)}")

    spotify_podcasts_with_emails = []
    logger.info("Extracting emails from Spotify podcast links...")
    for podcast in spotify_podcasts_raw:
        logger.info(f"Extracting from: {podcast[KEY_TITLE]} - {podcast[KEY_URL]}")
        info = extract_info_from_url(podcast[KEY_URL])
        if info[KEY_EMAILS]:
            spotify_podcasts_with_emails.append({
                KEY_TITLE: podcast[KEY_TITLE],
                KEY_URL: podcast[KEY_URL],
                KEY_PUBLISHER: podcast[KEY_PUBLISHER],
                KEY_EMAILS: info[KEY_EMAILS]
            })
        else:
            logger.info(f"Skipping '{podcast[KEY_TITLE]}' (no valid emails found via scraping).")

    logger.info(f"Found {len(spotify_podcasts_with_emails)} Spotify podcasts with emails after scraping.")

    logger.info("Fetching data from Azure DB...")
    db_podcasts_data = fetch_data_from_azure_db(AZURE_DB_CONTAINER, AZURE_DB_BLOB_PATH)

    logger.info("Combining and de-duplicating podcast data...")
    combined_data = {}

    for podcast in spotify_podcasts_with_emails:
        url = podcast.get(KEY_URL)
        if url:
            podcast[KEY_EMAILS] = list(set(podcast.get(KEY_EMAILS, [])))
            combined_data[url] = podcast

    added_from_db = 0
    skipped_duplicates = 0
    for podcast in db_podcasts_data:
        url = podcast.get(KEY_URL)
        if url:
            if url not in combined_data:
                podcast[KEY_EMAILS] = list(set(podcast.get(KEY_EMAILS, [])))
                combined_data[url] = podcast
                added_from_db += 1
            else:
                skipped_duplicates += 1

    if skipped_duplicates > 0:
        logger.info(f"Skipped {skipped_duplicates} duplicate podcasts found in the database (already present from Spotify scraping).")

    podcasts_for_xml = list(combined_data.values())
    logger.info(f"Total unique podcasts for XML: {len(podcasts_for_xml)} ({len(spotify_podcasts_with_emails)} from Spotify scrape, {added_from_db} added from DB)")

    if podcasts_for_xml:
        logger.info("Generating XML file...")
        root = ET.Element("podcasts")

        for podcast in podcasts_for_xml:
            podcast_elem = ET.SubElement(root, "podcast")
            ET.SubElement(podcast_elem, KEY_TITLE).text = podcast.get(KEY_TITLE, "")
            ET.SubElement(podcast_elem, KEY_URL).text = podcast.get(KEY_URL, "")
            ET.SubElement(podcast_elem, KEY_PUBLISHER).text = podcast.get(KEY_PUBLISHER, "")
            emails_elem = ET.SubElement(podcast_elem, KEY_EMAILS)
            for email in podcast.get(KEY_EMAILS, []):
                ET.SubElement(emails_elem, "email").text = email

        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml_str = dom.toprettyxml(indent="  ")

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
        output_filename = os.path.join(project_root, "scraped.xml")

        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(pretty_xml_str)
            logger.info(f"✅ Podcast data successfully saved to {output_filename}")
        except IOError as e:
            logger.error(f"❌ Error writing XML file: {e}", exc_info=True)
    else:
        logger.info("ℹ️ No podcasts with emails found from any source to save to XML.")
