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
import sqlite3
import tempfile
import logging
import time
import hashlib
import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from blob_storage import download_blob_to_tempfile

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

AZURE_DB_CONTAINER = "podmanagerfiles"
AZURE_DB_BLOB_PATH = "scrapeDb/podcastindex_feeds.db"

KEY_TITLE = "title"
KEY_RSS_URL = "rss"
KEY_SOURCE_URL = "url"
KEY_PUBLISHER = "publisher"
KEY_EMAILS = "emails"

EMAIL_FIND_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
EMAIL_VALIDATE_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?![a-zA-Z0-9])$", re.UNICODE)
EMAIL_EXTRACT_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.UNICODE)
RSS_FIND_PATTERN = re.compile(r'https?://[^\s<>"\']+\.(?:rss|xml)\b|https?://[^\s<>"\']*(?:feed|rss)[^\s<>"\']*', re.IGNORECASE | re.UNICODE)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

PODCASTINDEX_KEY = os.getenv("PODCAST_INDEX_KEY")
PODCASTINDEX_SECRET = os.getenv("PODCAST_INDEX_SECRET")
SCRAPE_DB_URI = os.getenv("SCRAPE_DB_URI")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
CACHE_FILE_PATH = os.path.join(PROJECT_ROOT, "scrape_cache.json")

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

def find_rss_in_text(text):
    if not text:
        return None
    match = RSS_FIND_PATTERN.search(text)
    if match:
        rss_url = match.group(0)
        if rss_url.lower().startswith("http"):
            logger.debug(f"Found potential RSS feed in text: {rss_url}")
            return rss_url
    return None

def is_valid_url(url):
    return url and url.lower().startswith(('http://', 'https://'))

def fetch_spotify_podcasts(target_count=None): 
    search_queries = [
        "podcast",
        "news podcast",
        "music podcast",
        "tech podcast",
        "sports podcast",
        "health podcast",
        "comedy podcast",
        "business podcast",
        "education podcast",
        "science podcast",
        "history podcast",
        "true crime podcast",
        "interview",
        "storytelling",
        "technology",
        "finance",
        "politics",
        "culture",
        "arts",
        "self-improvement"
    ]
    podcasts = set()
    limit = 50
    max_offset = 1000

    if target_count is None:
        logger.info("🎯 Fetching all possible unique podcasts from Spotify (up to API limits).")
    else:
        logger.info(f"🎯 Fetching a maximum of {target_count} unique podcasts for testing.")

    for query in search_queries:
        offset = 0
        logger.info(f"Searching for podcasts with query: '{query}'")

        while offset < max_offset:
            if target_count is not None and len(podcasts) >= target_count:
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
                description = item.get('description', '')
                rss_url_from_desc = find_rss_in_text(description)

                podcast_entry = (
                    item["name"],
                    item["external_urls"]["spotify"],
                    item.get("publisher", ""),
                    rss_url_from_desc,
                    description
                )
                podcasts.add(podcast_entry)

                if target_count is not None and len(podcasts) >= target_count:
                    logger.info(f"🏁 Target of {target_count} podcasts reached.")
                    break

            newly_added = len(podcasts) - initial_count
            logger.info(f"Fetched {newly_added} new unique podcasts from this batch. Total unique: {len(podcasts)}")

            if target_count is not None and len(podcasts) >= target_count:
                break

            offset += limit

        if target_count is not None and len(podcasts) >= target_count:
            logger.info(f"🏁 Target of {target_count} podcasts reached. Stopping all searches.")
            break

    podcast_list = [{
        KEY_TITLE: p[0],
        KEY_SOURCE_URL: p[1],
        KEY_PUBLISHER: p[2],
        KEY_RSS_URL: p[3],
        'description': p[4]
    } for p in podcasts]

    if target_count is None:
        return podcast_list
    else:
        return podcast_list[:target_count]

def extract_info_from_url(url):
    emails_found = []
    rss_url_found = None
    page_title = "No title found"

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            page_title = soup.title.string.strip() if soup.title else "No title found"
            page_text = soup.get_text()

            potential_emails = re.findall(EMAIL_FIND_PATTERN, page_text)
            logger.debug(f"URL: {url} - Potential email candidates: {potential_emails}")
            cleaned_emails_set = set()
            for candidate in potential_emails:
                candidate = candidate.strip()
                match = EMAIL_EXTRACT_PATTERN.match(candidate)
                if match:
                    extracted_email = match.group(0)
                    if EMAIL_VALIDATE_PATTERN.match(extracted_email):
                        cleaned_emails_set.add(extracted_email)
            emails_found = list(cleaned_emails_set)
            if emails_found:
                logger.info(f"URL: {url} - Found emails: {emails_found}")
            else:
                logger.debug(f"URL: {url} - No valid emails found.")

            link_tag = soup.find('link', {'type': 'application/rss+xml', 'href': True})
            if link_tag:
                rss_url_found = link_tag['href']
                if not is_valid_url(rss_url_found):
                    rss_url_found = None

            if not rss_url_found:
                rss_url_found = find_rss_in_text(page_text)
                if rss_url_found:
                    logger.info(f"URL: {url} - Found potential RSS feed via text search: {rss_url_found}")

            return {KEY_EMAILS: emails_found, KEY_RSS_URL: rss_url_found, KEY_TITLE: page_title}
        else:
            logger.error(f"Failed to fetch {url}, status code: {response.status_code}")
            return {KEY_EMAILS: [], KEY_RSS_URL: None, KEY_TITLE: page_title}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return {KEY_EMAILS: [], KEY_RSS_URL: None, KEY_TITLE: page_title}

def fetch_data_from_azure_db(container_name, blob_path):
    logger.info(f"Attempting to process database from Azure Blob: {container_name}/{blob_path}")
    filtered_db_podcasts = []
    temp_db_path = None

    try:
        temp_db_path = download_blob_to_tempfile(container_name, blob_path)
        if not temp_db_path:
            return filtered_db_podcasts

        conn = None
        try:
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            logger.info(f"Connected to temporary SQLite database: {temp_db_path}")

            query = "SELECT title, url, author, ownerEmail FROM feeds WHERE ownerEmail IS NOT NULL AND ownerEmail != ''"
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info(f"Found {len(rows)} potential podcasts in the database with non-empty ownerEmail.")

            for row in rows:
                title, feed_url, publisher, email_str = row
                final_email_to_add = None
                is_feed_url_valid = False

                if feed_url:
                    feed_url = feed_url.strip()
                    if is_valid_url(feed_url):
                        is_feed_url_valid = True

                if email_str:
                    cleaned_email_str = email_str.strip()
                    match = EMAIL_EXTRACT_PATTERN.match(cleaned_email_str)
                    if match:
                        extracted_email = match.group(0)
                        if EMAIL_VALIDATE_PATTERN.match(extracted_email):
                            final_email_to_add = extracted_email

                if final_email_to_add and is_feed_url_valid:
                    filtered_db_podcasts.append({
                        KEY_TITLE: title.strip(),
                        KEY_RSS_URL: feed_url,
                        KEY_SOURCE_URL: feed_url,
                        KEY_PUBLISHER: publisher.strip() if publisher else "",
                        KEY_EMAILS: [final_email_to_add]
                    })

        except sqlite3.Error as db_err:
            logger.error(f"Database error processing {temp_db_path}: {db_err}", exc_info=True)
        finally:
            if conn:
                conn.close()

    except Exception as e:
        logger.error(f"An unexpected error occurred during DB processing: {e}", exc_info=True)
    finally:
        if temp_db_path and os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
                logger.info(f"Removed temporary database file: {temp_db_path}")
            except OSError as remove_err:
                logger.error(f"Error removing temporary file {temp_db_path}: {remove_err}")

    logger.info(f"Returning {len(filtered_db_podcasts)} podcasts processed and filtered from the database.")
    return filtered_db_podcasts

def fetch_podcastindex_data(max_feeds=1000):
    logger.info(f"Attempting to fetch up to {max_feeds} recent feeds from Podcast Index API...")
    podcastindex_podcasts = []

    if not PODCASTINDEX_KEY or not PODCASTINDEX_SECRET:
        logger.error("Podcast Index API Key or Secret not found in environment variables.")
        return podcastindex_podcasts

    api_header_time = str(int(time.time()))
    data_to_hash = PODCASTINDEX_KEY + PODCASTINDEX_SECRET + api_header_time
    sha1_hash = hashlib.sha1(data_to_hash.encode('utf-8')).hexdigest()

    headers = {
        'X-Auth-Date': api_header_time,
        'X-Auth-Key': PODCASTINDEX_KEY,
        'Authorization': sha1_hash,
        'User-Agent': 'PodManager.ai/1.0'
    }

    api_url = f"https://api.podcastindex.org/api/1.0/recent/feeds?max={max_feeds}&pretty"

    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data.get('status') != 'true':
            logger.error(f"Podcast Index API returned error status: {data.get('description', 'Unknown error')}")
            return podcastindex_podcasts

        feeds = data.get('feeds', [])
        logger.info(f"Received {len(feeds)} feeds from Podcast Index API.")

        for feed in feeds:
            title = feed.get('title')
            rss_url = feed.get('url')
            email_str = feed.get('ownerEmail')
            publisher = feed.get('author')

            final_email_to_add = None
            is_feed_url_valid = False

            if rss_url:
                rss_url = rss_url.strip()
                if is_valid_url(rss_url):
                    is_feed_url_valid = True

            if email_str:
                cleaned_email_str = email_str.strip()
                match = EMAIL_EXTRACT_PATTERN.match(cleaned_email_str)
                if match:
                    extracted_email = match.group(0)
                    if EMAIL_VALIDATE_PATTERN.match(extracted_email):
                        final_email_to_add = extracted_email

            if final_email_to_add and is_feed_url_valid:
                podcastindex_podcasts.append({
                    KEY_TITLE: title.strip() if title else "",
                    KEY_RSS_URL: rss_url,
                    KEY_SOURCE_URL: rss_url,
                    KEY_PUBLISHER: publisher.strip() if publisher else "",
                    KEY_EMAILS: [final_email_to_add]
                })

    except requests.exceptions.RequestException as e:
        logger.error(f"Error during Podcast Index API request: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error processing Podcast Index data: {e}", exc_info=True)

    logger.info(f"Returning {len(podcastindex_podcasts)} podcasts processed and filtered from Podcast Index.")
    return podcastindex_podcasts

def get_existing_user_podcast_rss_urls():
    existing_rss_urls = set()
    if not SCRAPE_DB_URI:
        logger.error("SCRAPE_DB_URI not found in environment variables. Cannot check for existing user podcasts.")
        return existing_rss_urls

    try:
        db_name = SCRAPE_DB_URI.split('/')[-1].split('?')[0] if '/' in SCRAPE_DB_URI else "PodmanagerLive"
        logger.info(f"Connecting to MongoDB Live ({db_name}) for exclusion check...")
        client = MongoClient(SCRAPE_DB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
        db = client[db_name]
        users_collection = db['users']

        pipeline = [
            {'$unwind': '$podcasts'},
            {'$match': {'podcasts.rss_url': {'$exists': True, '$ne': None, '$ne': ''}}},
            {'$group': {'_id': '$podcasts.rss_url'}}
        ]
        results = users_collection.aggregate(pipeline)

        for doc in results:
            existing_rss_urls.add(doc['_id'])

        logger.info(f"Found {len(existing_rss_urls)} unique RSS URLs associated with existing users.")
        client.close()

    except ConnectionFailure:
        logger.error("MongoDB connection failed. Cannot check for existing user podcasts.", exc_info=True)
    except ConfigurationError as ce:
        logger.error(f"MongoDB configuration error: {ce}. Cannot check for existing user podcasts.", exc_info=True)
    except Exception as e:
        logger.error(f"Error fetching existing user podcast RSS URLs from MongoDB: {e}", exc_info=True)

    return existing_rss_urls

def load_cache(cache_path):
    default_data = {
        "filtered_spotify_podcasts": [],
        "filtered_db_podcasts": [],
        "filtered_podcastindex_podcasts": [],
    }
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key in default_data:
                    if key not in data:
                        data[key] = default_data[key]
                logger.info(f"✅ Successfully loaded cache from {cache_path}")
                return data
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Cache file {cache_path} is corrupted. Starting fresh.")
            return default_data
        except IOError as e:
            logger.error(f"❌ Error reading cache file {cache_path}: {e}. Starting fresh.")
            return default_data
    else:
        logger.info("ℹ️ No cache file found. Starting fresh.")
        return default_data

def save_cache(cache_path, data):
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"✅ Progress saved to cache file: {cache_path}")
    except IOError as e:
        logger.error(f"❌ Error writing cache file {cache_path}: {e}")
    except TypeError as e:
        logger.error(f"❌ Error serializing data for cache: {e}")

def clear_cache(cache_path):
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            logger.info(f"✅ Cache file {cache_path} cleared.")
        except OSError as e:
            logger.error(f"❌ Error deleting cache file {cache_path}: {e}")

if __name__ == "__main__":
    logger.info("--- Starting Podcast Scraping ---")

    cached_data = load_cache(CACHE_FILE_PATH)
    filtered_spotify_podcasts = cached_data["filtered_spotify_podcasts"]
    filtered_db_podcasts = cached_data["filtered_db_podcasts"]
    filtered_podcastindex_podcasts = cached_data["filtered_podcastindex_podcasts"]

    if not filtered_spotify_podcasts:
        logger.info("Fetching Spotify podcasts (Full Scrape)...")
        spotify_podcasts_raw = fetch_spotify_podcasts(target_count=None)
        logger.info(f"Fetched {len(spotify_podcasts_raw)} raw podcasts from Spotify.")

        processed_spotify_list = []
        logger.info("Processing Spotify podcasts: Scraping pages for emails/RSS and filtering...")
        for podcast_data in spotify_podcasts_raw:
            source_url = podcast_data[KEY_SOURCE_URL]
            logger.debug(f"Processing Spotify item: {podcast_data[KEY_TITLE]} ({source_url})")

            scraped_info = extract_info_from_url(source_url)
            podcast_data[KEY_EMAILS] = scraped_info[KEY_EMAILS]

            if not podcast_data.get(KEY_RSS_URL) and scraped_info.get(KEY_RSS_URL):
                logger.info(f"Found RSS feed '{scraped_info[KEY_RSS_URL]}' via scraping for '{podcast_data[KEY_TITLE]}'")
                podcast_data[KEY_RSS_URL] = scraped_info[KEY_RSS_URL]

            has_valid_email = bool(podcast_data.get(KEY_EMAILS))
            has_valid_rss = is_valid_url(podcast_data.get(KEY_RSS_URL))

            if has_valid_email and has_valid_rss:
                podcast_data.pop('description', None)
                processed_spotify_list.append(podcast_data)
                logger.debug(f"KEEPING Spotify podcast: '{podcast_data[KEY_TITLE]}' (Email: Yes, RSS: Yes)")

        filtered_spotify_podcasts = processed_spotify_list
        logger.info(f"Found {len(filtered_spotify_podcasts)} Spotify podcasts meeting criteria (valid email & RSS).")

        save_cache(CACHE_FILE_PATH, {
            "filtered_spotify_podcasts": filtered_spotify_podcasts,
            "filtered_db_podcasts": filtered_db_podcasts,
            "filtered_podcastindex_podcasts": filtered_podcastindex_podcasts,
        })
    else:
        logger.info("ℹ️ Skipping Spotify fetching/processing - data loaded from cache.")

    if not filtered_db_podcasts:
        logger.info("Fetching and filtering data from Azure DB...")
        filtered_db_podcasts = fetch_data_from_azure_db(AZURE_DB_CONTAINER, AZURE_DB_BLOB_PATH)
        save_cache(CACHE_FILE_PATH, {
            "filtered_spotify_podcasts": filtered_spotify_podcasts,
            "filtered_db_podcasts": filtered_db_podcasts,
            "filtered_podcastindex_podcasts": filtered_podcastindex_podcasts,
        })
    else:
        logger.info("ℹ️ Skipping Azure DB fetching - data loaded from cache.")

    if not filtered_podcastindex_podcasts:
        logger.info("Fetching and filtering data from Podcast Index API...")
        filtered_podcastindex_podcasts = fetch_podcastindex_data(max_feeds=5000)
        save_cache(CACHE_FILE_PATH, {
            "filtered_spotify_podcasts": filtered_spotify_podcasts,
            "filtered_db_podcasts": filtered_db_podcasts,
            "filtered_podcastindex_podcasts": filtered_podcastindex_podcasts,
        })
    else:
        logger.info("ℹ️ Skipping Podcast Index fetching - data loaded from cache.")

    logger.info("Fetching existing user podcast associations from Live MongoDB...")
    existing_user_rss = get_existing_user_podcast_rss_urls()

    logger.info("Combining and de-duplicating podcast data...")
    combined_data = {}
    processed_sources = {"spotify": 0, "db": 0, "podcastindex": 0}
    duplicates_merged = 0

    for podcast in filtered_spotify_podcasts:
        rss_url = podcast.get(KEY_RSS_URL)
        if rss_url and rss_url not in combined_data:
            combined_data[rss_url] = podcast
            processed_sources["spotify"] += 1
        elif rss_url:
            logger.warning(f"Duplicate RSS URL '{rss_url}' (Spotify vs existing). Merging emails for '{podcast.get(KEY_TITLE)}'.")
            existing_emails = set(combined_data[rss_url].get(KEY_EMAILS, []))
            new_emails = set(podcast.get(KEY_EMAILS, []))
            combined_data[rss_url][KEY_EMAILS] = list(existing_emails.union(new_emails))
            duplicates_merged += 1

    for podcast in filtered_db_podcasts:
        rss_url = podcast.get(KEY_RSS_URL)
        if rss_url and rss_url not in combined_data:
            combined_data[rss_url] = podcast
            processed_sources["db"] += 1
        elif rss_url:
            logger.warning(f"Duplicate RSS URL '{rss_url}' (DB vs existing). Merging emails for '{podcast.get(KEY_TITLE)}'.")
            existing_emails = set(combined_data[rss_url].get(KEY_EMAILS, []))
            new_emails = set(podcast.get(KEY_EMAILS, []))
            combined_data[rss_url][KEY_EMAILS] = list(existing_emails.union(new_emails))
            duplicates_merged += 1

    for podcast in filtered_podcastindex_podcasts:
        rss_url = podcast.get(KEY_RSS_URL)
        if rss_url and rss_url not in combined_data:
            combined_data[rss_url] = podcast
            processed_sources["podcastindex"] += 1
        elif rss_url:
            logger.warning(f"Duplicate RSS URL '{rss_url}' (PodcastIndex vs existing). Merging emails for '{podcast.get(KEY_TITLE)}'.")
            existing_emails = set(combined_data[rss_url].get(KEY_EMAILS, []))
            new_emails = set(podcast.get(KEY_EMAILS, []))
            combined_data[rss_url][KEY_EMAILS] = list(existing_emails.union(new_emails))
            duplicates_merged += 1

    if duplicates_merged > 0:
        logger.info(f"Merged email data for {duplicates_merged} duplicate podcasts found based on RSS URL.")

    logger.info("Filtering combined data against existing user podcasts...")
    podcasts_for_xml = []
    excluded_count = 0
    for rss_url, podcast_data in combined_data.items():
        if rss_url in existing_user_rss:
            logger.debug(f"Excluding podcast '{podcast_data.get(KEY_TITLE)}' (RSS: {rss_url}) as it's linked to an existing user.")
            excluded_count += 1
        else:
            podcasts_for_xml.append(podcast_data)

    logger.info(f"Excluded {excluded_count} podcasts already associated with users.")
    logger.info(f"Total unique podcasts for XML after exclusion: {len(podcasts_for_xml)}")

    if podcasts_for_xml:
        logger.info("Generating XML file...")
        root = ET.Element("podcasts")

        for podcast in podcasts_for_xml:
            podcast_elem = ET.SubElement(root, "podcast")
            ET.SubElement(podcast_elem, KEY_TITLE).text = podcast.get(KEY_TITLE, "")
            ET.SubElement(podcast_elem, KEY_RSS_URL).text = podcast.get(KEY_RSS_URL, "")
            ET.SubElement(podcast_elem, KEY_SOURCE_URL).text = podcast.get(KEY_SOURCE_URL, "")
            ET.SubElement(podcast_elem, KEY_PUBLISHER).text = podcast.get(KEY_PUBLISHER, "")
            emails_elem = ET.SubElement(podcast_elem, KEY_EMAILS)
            for email in podcast.get(KEY_EMAILS, []):
                ET.SubElement(emails_elem, "email").text = email

        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml_str = dom.toprettyxml(indent="  ")

        output_filename = os.path.join(PROJECT_ROOT, "scraped.xml")

        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(pretty_xml_str)
            logger.info(f"✅ Podcast data successfully saved to {output_filename}")
            clear_cache(CACHE_FILE_PATH)
        except IOError as e:
            logger.error(f"❌ Error writing XML file: {e}", exc_info=True)
    else:
        logger.info("ℹ️ No podcasts meeting criteria (valid email & RSS, not existing user) found to save to XML.")
        clear_cache(CACHE_FILE_PATH)

    logger.info("--- Scraping Finished ---")
