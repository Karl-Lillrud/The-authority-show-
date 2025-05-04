from __future__ import annotations # Ensure this is the first line

import pymongo.uri_parser # For robust DB name parsing
import requests
import hashlib
import json # For caching
import logging
import os
import re
import sqlite3
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
import spotipy

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, Any # Added Any
from xml.dom import minidom
from requests.adapters import HTTPAdapter # For retries
from urllib3.util.retry import Retry # For retries
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure
from spotipy.oauth2 import SpotifyOAuth
# Use relative import for blob_storage
from .blob_storage import download_blob_to_tempfile, get_blob_service_client # Import client getter
# Use relative import for rss_Service
from ..services.rss_Service import RSSService

load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Constants ---
RSS_FIND_PATTERN = re.compile(r'https?://[^\s<>"\']+\.(?:rss|xml)\b|https?://[^\s<>"\']*(?:feed|rss)[^\s<>"\']*', re.IGNORECASE | re.UNICODE)
# Stricter validation pattern for extracted emails
EMAIL_VALIDATE_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", re.UNICODE)
# Keep extraction pattern broad initially
EMAIL_EXTRACT_PATTERN = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", re.UNICODE)

KEY_TITLE = "title"
KEY_RSS_URL = "rss"
KEY_SOURCE_URL = "url"
KEY_PUBLISHER = "publisher"
KEY_EMAILS = "emails"

AZURE_CONTAINER = "podmanagerfiles"
AZURE_DB_BLOB = "scrapeDb/podcastindex_feeds.db"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
CACHE_PATH = os.path.join(PROJECT_ROOT, "scrape_cache.json") # Use PROJECT_ROOT

THREADS = int(os.getenv("SCRAPER_THREADS", "32")) # Reduced default threads

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

PODCASTINDEX_KEY = os.getenv("PODCAST_INDEX_KEY")
PODCASTINDEX_SECRET = os.getenv("PODCAST_INDEX_SECRET")
SCRAPE_DB_URI = os.getenv("SCRAPE_DB_URI")

# --- Spotify Auth ---
try:
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-read-email",
            open_browser=True # Keep True if manual auth is needed first time
        )
    )
    sp.current_user()
    logger.info("✅ Successfully authenticated with Spotify.")
except Exception as e:
    logger.error(f"❌ Spotify Authentication Failed: {e}", exc_info=True) # Add exc_info
    sys.exit(1)

# --- Helper Functions ---
def looks_like_potential_rss(url: str | None) -> bool:
    """Quick check if a URL might be an RSS feed based on pattern."""
    return bool(url and RSS_FIND_PATTERN.search(url))

def clean_emails(emails: List[str]) -> List[str]:
    """Extracts and validates email addresses, removing trailing junk."""
    seen: Set[str] = set()
    for raw in emails:
        # Find all potential matches first
        potential_matches = EMAIL_EXTRACT_PATTERN.findall(raw)
        for potential in potential_matches:
            # Validate each potential match strictly
            if EMAIL_VALIDATE_PATTERN.fullmatch(potential):
                seen.add(potential.lower())
    return list(seen)

def is_valid_url(url: str | None) -> bool:
    """Checks if a URL starts with http:// or https://."""
    return bool(url and url.lower().startswith(('http://', 'https://')))

# --- Session with Retries ---
def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 503, 504), # Retry on these server errors
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# --- Scraping Function (Renamed from extract_info_from_url) ---
def scrape_page(url: str) -> Dict[str, Any]:
    """Return emails + rss found on a Spotify show page, with retries."""
    headers = {"User-Agent": "Mozilla/5.0"}
    session = requests_retry_session()
    page_title = "No title found" # Keep title for context if needed
    try:
        resp = session.get(url, headers=headers, timeout=15) # Increased timeout
        resp.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx) after retries

    except requests.exceptions.RequestException as exc:
        logger.error("Error retrieving %s after retries: %s", url, exc)
        # Return empty dict but maybe keep title if available before error?
        # For simplicity, return empty on complete failure.
        return {KEY_EMAILS: [], KEY_RSS_URL: None, KEY_TITLE: page_title}

    soup = BeautifulSoup(resp.text, "html.parser")
    page_title = soup.title.string.strip() if soup.title else "No title found"
    text = soup.get_text(" ")

    # Use the improved clean_emails function
    emails = clean_emails(EMAIL_EXTRACT_PATTERN.findall(text))
    if emails:
        logger.info(f"URL: {url} - Found emails: {emails}")
    else:
        logger.debug(f"URL: {url} - No valid emails found.")


    rss: Optional[str] = None
    link_tag = soup.find("link", {"type": "application/rss+xml", "href": True})
    # Check if href exists and looks like a valid URL before checking pattern
    if link_tag and link_tag.get("href") and is_valid_url(link_tag["href"]):
        href = link_tag["href"].strip()
        # Use the flexible pattern check
        if looks_like_potential_rss(href):
            rss = href
            logger.info(f"URL: {url} - Found RSS feed via <link> tag: {rss}")


    if not rss:
        # Fallback to regex scan on page text (use find_rss_in_text logic here)
        match = RSS_FIND_PATTERN.search(text)
        if match:
            potential_rss = match.group(0).strip()
            if is_valid_url(potential_rss): # Ensure it's a valid URL format
                rss = potential_rss
                logger.info(f"URL: {url} - Found potential RSS feed via text search: {rss}")

    # Final check if found RSS is a valid URL format
    if rss and not is_valid_url(rss):
        logger.warning("Ignoring invalid RSS URL format '%s' found on %s", rss, url)
        rss = None

    return {KEY_EMAILS: emails, KEY_RSS_URL: rss, KEY_TITLE: page_title} # Return title too

# --- Spotify Fetching ---
def fetch_spotify_catalogue(limit_per_query: int = 50, max_offset: int = 1_000) -> List[Dict[str, Any]]:
    queries = [
        "podcast", "news podcast", "music podcast", "tech podcast", "sports podcast",
        "health podcast", "comedy podcast", "business podcast", "education podcast",
        "science podcast", "history podcast", "true crime podcast", "interview",
        "storytelling", "technology", "finance", "politics", "culture", "arts",
        "self-improvement"
    ]
    seen_ids: Set[str] = set()
    shows: List[Dict[str, Any]] = []
    api_call_delay = 0.5 # seconds

    for q in queries:
        logger.info(f"Spotify: Searching for query '{q}'...")
        for offset in range(0, max_offset, limit_per_query):
            try:
                results = sp.search(q=q, type="show", limit=limit_per_query, offset=offset)
                time.sleep(api_call_delay) # Delay after successful call
            except spotipy.SpotifyException as e:
                logger.error(f"Spotify API error for query '{q}' offset {offset}: {e}")
                sleep_time = api_call_delay # Default delay
                if e.http_status == 429:
                    sleep_time = 60 # Longer sleep for rate limit
                    logger.warning(f"Rate limited by Spotify API. Sleeping for {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    continue # Retry this offset
                else:
                    time.sleep(sleep_time) # Short delay before breaking
                    break
            except Exception as e:
                logger.error(f"Unexpected error during Spotify search for '{q}': {e}", exc_info=True)
                time.sleep(api_call_delay) # Short delay before breaking
                break

            items = results.get("shows", {}).get("items", [])
            if not items:
                logger.info(f"Spotify: No more items for query '{q}' at offset {offset}.")
                break

            initial_count = len(shows)
            for item in items:
                if item["id"] not in seen_ids:
                    seen_ids.add(item["id"])
                    # Don't extract RSS from description here, do it during page scrape
                    shows.append(
                        {
                            KEY_TITLE: item["name"],
                            KEY_SOURCE_URL: item["external_urls"]["spotify"],
                            KEY_PUBLISHER: item.get("publisher", ""),
                            KEY_RSS_URL: None, # Will be found during scrape_page
                            KEY_EMAILS: [],
                            # Keep description temporarily for context if needed, remove later
                            'description': item.get('description', '')
                        }
                    )
            newly_added = len(shows) - initial_count
            logger.info(f"Spotify: Fetched {newly_added} new unique shows from this batch (Query: '{q}', Offset: {offset}). Total unique: {len(shows)}")

    logger.info("Collected %d unique Spotify show URLs", len(shows))
    return shows

# --- Azure DB Fetching ---
def fetch_data_from_azure_db(container_name, blob_path) -> List[Dict[str, Any]]:
    logger.info(f"Attempting to process database from Azure Blob: {container_name}/{blob_path}")
    filtered_db_podcasts = []
    temp_db_path = None

    # Get client inside function to ensure it's initialized when needed
    blob_service_client = get_blob_service_client()
    if not blob_service_client:
        logger.error("Failed to initialize Azure Blob Service Client. Skipping Azure DB step.")
        return []

    try:
        # Pass the initialized client to the download function
        temp_db_path = download_blob_to_tempfile(container_name, blob_path, blob_service_client)
        if not temp_db_path:
            logger.warning("Failed to download Azure DB blob. Skipping Azure DB step.")
            return filtered_db_podcasts # Return empty list

        conn = None
        try:
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            logger.info(f"Connected to temporary SQLite database: {temp_db_path}")

            query = "SELECT title, url, author, ownerEmail FROM feeds WHERE ownerEmail IS NOT NULL AND ownerEmail != ''"
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info(f"Azure DB: Found {len(rows)} potential rows with email.")

            for row in rows:
                title, feed_url, publisher, email_str = row

                # Validate URL
                feed_url = feed_url.strip() if feed_url else None
                is_feed_url_valid = is_valid_url(feed_url)

                # Validate Email
                cleaned_emails = clean_emails([email_str] if email_str else [])

                if cleaned_emails and is_feed_url_valid:
                    filtered_db_podcasts.append({
                        KEY_TITLE: title.strip() if title else "",
                        KEY_RSS_URL: feed_url,
                        KEY_SOURCE_URL: feed_url, # Use RSS as source URL for DB entries
                        KEY_PUBLISHER: publisher.strip() if publisher else "",
                        KEY_EMAILS: cleaned_emails # Use the cleaned list
                    })
                else:
                    reason = []
                    if not cleaned_emails: reason.append("invalid/missing email")
                    if not is_feed_url_valid: reason.append("invalid/missing feed URL")
                    logger.warning(f"Skipping DB entry '{title}' due to: {', '.join(reason)}. Email='{email_str}', Feed='{feed_url}'")

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

# --- Podcast Index Fetching ---
def fetch_podcastindex_data(max_feeds=1000) -> List[Dict[str, Any]]:
    logger.info(f"Attempting to fetch up to {max_feeds} recent feeds from Podcast Index API...")
    podcastindex_podcasts = []

    if not PODCASTINDEX_KEY or not PODCASTINDEX_SECRET:
        logger.error("Podcast Index API Key or Secret not found in environment variables.")
        return podcastindex_podcasts

    # ... (API auth headers setup remains the same) ...
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
        session = requests_retry_session() # Use retry session
        response = session.get(api_url, headers=headers, timeout=30)
        response.raise_for_status() # Check for HTTP errors

        data = response.json()

        if data.get('status') != 'true':
            logger.error(f"Podcast Index API returned error status: {data.get('description', 'Unknown error')}")
            return podcastindex_podcasts

        feeds = data.get('feeds', [])
        logger.info(f"Received {len(feeds)} feeds from Podcast Index API.")

        processed_count = 0
        skipped_email = 0
        skipped_rss = 0
        rss_fetch_attempts = 0
        rss_fetch_success_email = 0

        for feed in feeds:
            title = feed.get('title')
            rss_url = feed.get('url')
            email_str = feed.get('ownerEmail')
            publisher = feed.get('author')

            # Validate URL first
            rss_url = rss_url.strip() if rss_url else None
            is_feed_url_valid = is_valid_url(rss_url)

            # Validate Email from API data
            cleaned_emails = clean_emails([email_str] if email_str else [])

            # --- Fallback: Fetch RSS if email missing/invalid and URL is valid ---
            if not cleaned_emails and is_feed_url_valid:
                logger.info(f"Podcast Index: Email missing/invalid for '{title}'. Attempting to fetch RSS feed: {rss_url}")
                rss_fetch_attempts += 1
                # Use RSSService to fetch and parse the feed
                # Note: This adds significant overhead
                feed_data, status_code = RSSService.fetch_rss_feed(rss_url)
                if status_code == 200 and feed_data.get("email"):
                    rss_email = feed_data.get("email")
                    rss_cleaned_emails = clean_emails([rss_email])
                    if rss_cleaned_emails:
                        logger.info(f"Podcast Index: Found valid email '{rss_cleaned_emails[0]}' via RSS fetch for '{title}'.")
                        cleaned_emails = rss_cleaned_emails # Use email found from RSS
                        rss_fetch_success_email += 1
                    else:
                        logger.info(f"Podcast Index: Email '{rss_email}' found via RSS fetch for '{title}' was invalid after cleaning.")
                else:
                     logger.info(f"Podcast Index: Failed to fetch or find email in RSS feed for '{title}' (Status: {status_code}).")
            # --- End Fallback ---


            if cleaned_emails and is_feed_url_valid:
                podcastindex_podcasts.append({
                    KEY_TITLE: title.strip() if title else "",
                    KEY_RSS_URL: rss_url,
                    KEY_SOURCE_URL: rss_url, # Use RSS as source URL
                    KEY_PUBLISHER: publisher.strip() if publisher else "",
                    KEY_EMAILS: cleaned_emails
                })
                processed_count += 1
            else:
                reason = []
                # Check original email_str for logging context if fallback failed
                original_email_invalid = not clean_emails([email_str] if email_str else [])
                if original_email_invalid and not cleaned_emails: reason.append("invalid/missing email (API & RSS fetch)")
                elif not cleaned_emails: reason.append("invalid/missing email (API)") # Should not happen if fallback works, but good to cover
                if not is_feed_url_valid: reason.append("invalid/missing feed URL")

                logger.info(f"Skipping Podcast Index entry '{title}' due to: {', '.join(reason)}. API Email='{email_str}', Feed='{rss_url}'")
                # Count skips based on final state
                if not cleaned_emails: skipped_email += 1
                if not is_feed_url_valid: skipped_rss += 1


        logger.info(f"Podcast Index: Processed {processed_count} valid entries.")
        logger.info(f"Podcast Index: Attempted {rss_fetch_attempts} RSS fetches for missing emails, found {rss_fetch_success_email} valid emails.")
        logger.info(f"Podcast Index: Skipped {skipped_email} final entries for email, {skipped_rss} for RSS URL.")


    except requests.exceptions.RequestException as e:
        logger.error(f"Error during Podcast Index API request: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error processing Podcast Index data: {e}", exc_info=True)

    logger.info(f"Returning {len(podcastindex_podcasts)} podcasts processed and filtered from Podcast Index.")
    return podcastindex_podcasts

# --- MongoDB Exclusion ---
def get_existing_user_podcast_rss_urls() -> Set[str]:
    existing_rss_urls = set()
    if not SCRAPE_DB_URI:
        logger.error("SCRAPE_DB_URI not found in environment variables. Cannot check for existing user podcasts.")
        return existing_rss_urls

    try:
        # Use pymongo's parser for robustness
        parsed_uri = pymongo.uri_parser.parse_uri(SCRAPE_DB_URI)
        db_name = parsed_uri.get('database') # Returns None if not specified
        if not db_name:
            # Provide a default or raise an error if DB name is mandatory
            db_name = "PodmanagerLive" # Or raise ValueError("Database name missing in SCRAPE_DB_URI")
            logger.warning(f"Database name not found in SCRAPE_DB_URI, defaulting to '{db_name}'.")

        logger.info(f"Connecting to MongoDB '{db_name}' for exclusion check...")
        client = MongoClient(SCRAPE_DB_URI, serverSelectionTimeoutMS=5000)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster') # Replaced 'ping' with 'ismaster'
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

# --- Caching Functions ---
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
                # Ensure all keys exist, even if cache is partial/old
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

# --- Main Execution ---
if __name__ == "__main__":
    logger.info("--- Starting Podcast Scraping ---")

    # --- Load Cache ---
    cached_data = load_cache(CACHE_PATH)
    filtered_spotify_podcasts = cached_data["filtered_spotify_podcasts"]
    filtered_db_podcasts = cached_data["filtered_db_podcasts"] # Keep variable even if unused
    filtered_podcastindex_podcasts = cached_data["filtered_podcastindex_podcasts"]

    # --- 1. Azure DB (Commented out as requested) ---
    # if not filtered_db_podcasts:
    #     logger.info("Fetching and filtering data from Azure DB...")
    #     filtered_db_podcasts = fetch_data_from_azure_db(AZURE_CONTAINER, AZURE_DB_BLOB)
    #     save_cache(CACHE_PATH, { # Save progress
    #         "filtered_spotify_podcasts": filtered_spotify_podcasts,
    #         "filtered_db_podcasts": filtered_db_podcasts,
    #         "filtered_podcastindex_podcasts": filtered_podcastindex_podcasts,
    #     })
    # else:
    #     logger.info("ℹ️ Skipping Azure DB fetching - data loaded from cache.")
    logger.info("ℹ️ Skipping Azure DB fetching (step disabled).") # Add info message

    # --- 2. Podcast Index ---
    if not filtered_podcastindex_podcasts:
        logger.info("Fetching and filtering data from Podcast Index API...")
        # Fetch more feeds if possible, API limit might be higher
        filtered_podcastindex_podcasts = fetch_podcastindex_data(max_feeds=10000) # Increased max_feeds
        save_cache(CACHE_PATH, { # Save progress
            "filtered_spotify_podcasts": filtered_spotify_podcasts,
            "filtered_db_podcasts": filtered_db_podcasts, # Save empty list if skipped
            "filtered_podcastindex_podcasts": filtered_podcastindex_podcasts,
        })
    else:
        logger.info("ℹ️ Skipping Podcast Index fetching - data loaded from cache.")

    # --- 3. Spotify Fetch & Scrape ---
    if not filtered_spotify_podcasts:
        spotify_podcasts_raw = fetch_spotify_catalogue() # Renamed variable
        processed_spotify_list = []
        logger.info(f"Scraping {len(spotify_podcasts_raw)} Spotify pages concurrently (Threads: {THREADS})...")
        with ThreadPoolExecutor(max_workers=THREADS) as pool:
            # Map URLs to future objects, store original show dict as value
            future_to_show = {pool.submit(scrape_page, s[KEY_SOURCE_URL]): s for s in spotify_podcasts_raw}
            processed_count = 0
            for future in as_completed(future_to_show):
                show_original = future_to_show[future]
                url = show_original[KEY_SOURCE_URL]
                processed_count += 1
                if processed_count % 100 == 0: # Log progress periodically
                    logger.info(f"Spotify Scrape Progress: {processed_count}/{len(spotify_podcasts_raw)} pages processed.")
                try:
                    scraped_data = future.result()
                    # Merge scraped data (emails, potentially RSS) into original show dict
                    show_original[KEY_EMAILS] = scraped_data.get(KEY_EMAILS, [])
                    # Only update RSS if it wasn't found via description AND was found via scraping
                    # (RSS from description removed, so just check if scrape found one)
                    if scraped_data.get(KEY_RSS_URL):
                        show_original[KEY_RSS_URL] = scraped_data.get(KEY_RSS_URL)

                    # --- Filter scraped Spotify shows ---
                    has_valid_email = bool(show_original[KEY_EMAILS])
                    has_valid_rss = is_valid_url(show_original.get(KEY_RSS_URL))

                    if has_valid_email and has_valid_rss:
                        show_original.pop('description', None) # Remove description before adding
                        processed_spotify_list.append(show_original)
                        logger.debug(f"KEEPING Spotify podcast: '{show_original[KEY_TITLE]}' (Email: Yes, RSS: Yes)")
                    else:
                        # Log skips for Spotify items
                        reason = []
                        if not has_valid_email: reason.append("no valid email found")
                        if not has_valid_rss: reason.append("no valid RSS feed found")
                        logger.info(f"SKIPPING Spotify podcast: '{show_original.get(KEY_TITLE, 'N/A')}' ({', '.join(reason)})")


                except Exception as exc:
                    logger.error(f"Error processing result for {url}: {exc}", exc_info=True)

        filtered_spotify_podcasts = processed_spotify_list
        logger.info(f"Found {len(filtered_spotify_podcasts)} Spotify podcasts meeting criteria (valid email & RSS).")
        # Save progress after completing Spotify processing
        save_cache(CACHE_PATH, {
            "filtered_spotify_podcasts": filtered_spotify_podcasts,
            "filtered_db_podcasts": filtered_db_podcasts, # Save current state (likely empty)
            "filtered_podcastindex_podcasts": filtered_podcastindex_podcasts, # Save current state (likely empty)
        })
    else:
        logger.info("ℹ️ Skipping Spotify fetching/processing - data loaded from cache.")

    # --- 4. MongoDB Exclusion Check ---
    logger.info("Fetching existing user podcast associations from Live MongoDB...")
    existing_user_rss = get_existing_user_podcast_rss_urls() # Renamed variable

    # --- 5. Combine, De-duplicate, and Final Filter ---
    logger.info("Combining and de-duplicating podcast data...")
    combined_data: Dict[str, Dict[str, Any]] = {} # Use Any type hint
    duplicates_merged = 0

    # Combine lists (include commented-out Azure list for structure)
    all_sources = [
        ("PodcastIndex", filtered_podcastindex_podcasts),
        ("Spotify", filtered_spotify_podcasts),
    ]

    for source_name, podcast_list in all_sources:
        processed_count = 0
        for podcast in podcast_list:
            rss_url = podcast.get(KEY_RSS_URL)
            # Ensure RSS URL is valid before using as key
            if not rss_url or not isinstance(rss_url, str) or not is_valid_url(rss_url):
                logger.warning(f"Skipping item from {source_name} with invalid RSS URL: {podcast.get(KEY_TITLE)} - {rss_url}")
                continue

            existing = combined_data.get(rss_url)
            if not existing:
                combined_data[rss_url] = podcast
                processed_count += 1
            else:
                # Merge emails - ensure emails are cleaned
                existing_emails = set(existing.get(KEY_EMAILS, []))
                new_emails = set(podcast.get(KEY_EMAILS, [])) # Assume already cleaned
                merged_emails = list(existing_emails.union(new_emails))
                if len(merged_emails) > len(existing_emails):
                     logger.debug(f"Merging emails for duplicate RSS '{rss_url}' from {source_name}. Old: {existing_emails}, New: {new_emails}")
                     existing[KEY_EMAILS] = merged_emails
                     duplicates_merged += 1 # Count only if emails were actually added

        logger.info(f"Processed {processed_count} unique items from {source_name}.")

    if duplicates_merged > 0:
        logger.info(f"Merged email data for {duplicates_merged} duplicate podcasts found based on RSS URL.")

    logger.info(f"Total unique podcasts before exclusion: {len(combined_data)}")

    # --- 6. Exclude existing user feeds ---
    logger.info("Filtering combined data against existing user podcasts...")
    podcasts_for_xml = []
    excluded_count = 0
    for rss_url, podcast_data in combined_data.items():
        if rss_url in existing_user_rss: # Use renamed variable
            logger.debug(f"Excluding podcast '{podcast_data.get(KEY_TITLE)}' (RSS: {rss_url}) as it's linked to an existing user.")
            excluded_count += 1
        else:
            podcasts_for_xml.append(podcast_data)

    logger.info(f"Excluded {excluded_count} podcasts already associated with users.")
    logger.info(f"Total unique podcasts for XML after exclusion: {len(podcasts_for_xml)}")

    # --- 7. Generate XML ---
    if podcasts_for_xml:
        logger.info("Generating XML file...")
        root = ET.Element("podcasts")

        for podcast in podcasts_for_xml:
            podcast_elem = ET.SubElement(root, "podcast")
            # Ensure values are strings for XML
            ET.SubElement(podcast_elem, KEY_TITLE).text = str(podcast.get(KEY_TITLE, ""))
            ET.SubElement(podcast_elem, KEY_RSS_URL).text = str(podcast.get(KEY_RSS_URL, ""))
            emails_elem = ET.SubElement(podcast_elem, KEY_EMAILS)
            # Ensure emails are strings
            for email in podcast.get(KEY_EMAILS, []):
                ET.SubElement(emails_elem, "email").text = str(email)

        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml_str = dom.toprettyxml(indent="  ")

        # Use PROJECT_ROOT for output path
        output_filename = os.path.join(PROJECT_ROOT, "scraped.xml")

        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(pretty_xml_str)
            logger.info(f"✅ Podcast data successfully saved to {output_filename}")
            clear_cache(CACHE_PATH) # Clear cache on success
        except IOError as e:
            logger.error(f"❌ Error writing XML file: {e}", exc_info=True)
            # Keep cache if write fails
    else:
        logger.info("ℹ️ No podcasts meeting criteria found to save to XML.")
        clear_cache(CACHE_PATH) # Clear cache even if no results

    logger.info("--- Scraping Finished ---")


if __name__ == "__main__":
    main()
