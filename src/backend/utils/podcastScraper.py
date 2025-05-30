from __future__ import annotations  # Ensure this is the first line

import pymongo.uri_parser  # For robust DB name parsing
import requests
import hashlib
import json  # For caching
import logging
import os
import re
import sqlite3  # Re-add
import sys
import tempfile  # Re-add
import time
import xml.etree.ElementTree as ET
import spotipy

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, Any  # Added Any
from xml.dom import minidom
from requests.adapters import HTTPAdapter  # For retries
from urllib3.util.retry import Retry  # For retries
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure
from spotipy.oauth2 import SpotifyOAuth

# Use relative import for rss_Service
from ..services.rss_Service import RSSService

# Re-add blob_storage import
from .blob_storage import download_blob_to_tempfile, get_blob_service_client

load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Constants ---
RSS_FIND_PATTERN = re.compile(
    r'https?://[^\s<>"\']+\.(?:rss|xml)\b|https?://[^\s<>"\']*(?:feed|rss)[^\s<>"\']*',
    re.IGNORECASE | re.UNICODE,
)
EMAIL_VALIDATE_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", re.UNICODE
)
EMAIL_EXTRACT_PATTERN = re.compile(
    r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", re.UNICODE
)

KEY_TITLE = "title"
KEY_RSS_URL = "rss"
KEY_SOURCE_URL = "url"
KEY_PUBLISHER = "publisher"
KEY_EMAILS = "emails"

# Re-add Azure constants
AZURE_CONTAINER = "podmanagerfiles"
AZURE_DB_BLOB = "scrapeDb/podcastindex_feeds.db"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
CACHE_PATH = os.path.join(PROJECT_ROOT, "scrape_cache.json")  # Use consistent name

THREADS = int(os.getenv("SCRAPER_THREADS", "32"))

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
            open_browser=True,  # Keep True if manual auth is needed first time
        )
    )
    sp.current_user()
    logger.info("✅ Successfully authenticated with Spotify.")
except Exception as e:
    logger.error(
        f"❌ Spotify Authentication Failed: {e}", exc_info=True
    )  # Add exc_info
    sys.exit(1)


# --- Helper Functions ---
def looks_like_potential_rss(url: str | None) -> bool:
    """Quick check if a URL might be an RSS feed based on pattern."""
    return bool(url and RSS_FIND_PATTERN.search(url))


def clean_emails(emails: List[str]) -> List[str]:
    """Extracts and validates email addresses, removing trailing junk."""
    seen: Set[str] = set()
    for raw in emails:
        potential_matches = EMAIL_EXTRACT_PATTERN.findall(raw)
        for potential in potential_matches:
            if EMAIL_VALIDATE_PATTERN.fullmatch(potential):
                seen.add(potential.lower())
    return list(seen)


def is_valid_url(url: str | None) -> bool:
    """Checks if a URL starts with http:// or https://."""
    return bool(url and url.lower().startswith(("http://", "https://")))


# --- Session with Retries ---
def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 503, 504),  # Retry on these server errors
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
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# --- Scraping Function ---
def scrape_page(url: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Return emails + rss found on a Spotify show page or from its description, with retries."""
    emails: List[str] = []
    rss: Optional[str] = None
    page_title = "No title found"  # Default title

    # 1. Check description first if provided
    if description:
        logger.debug(f"Checking description for {url}...")
        desc_emails = clean_emails(EMAIL_EXTRACT_PATTERN.findall(description))
        if desc_emails:
            emails.extend(desc_emails)
            logger.info(f"URL: {url} - Found emails in description: {emails}")

        match = RSS_FIND_PATTERN.search(description)
        if match:
            potential_rss = match.group(0).strip()
            if is_valid_url(potential_rss):
                rss = potential_rss
                logger.info(
                    f"URL: {url} - Found potential RSS feed in description: {rss}"
                )

    # 2. If email or RSS still missing, scrape the page
    if not emails or not rss:
        logger.debug(
            f"Scraping full page for {url} (Email found: {bool(emails)}, RSS found: {bool(rss)})..."
        )
        headers = {"User-Agent": "Mozilla/5.0"}
        session = requests_retry_session()
        try:
            resp = session.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Error retrieving %s after retries: %s", url, exc)
            # Return whatever was found in description (if anything)
            return {KEY_EMAILS: emails, KEY_RSS_URL: rss, KEY_TITLE: page_title}

        soup = BeautifulSoup(resp.text, "html.parser")
        page_title = (
            soup.title.string.strip() if soup.title else "No title found"
        )  # Update title if page scraped
        text = soup.get_text(" ")

        # Find emails from page text if not already found
        if not emails:
            page_emails = clean_emails(EMAIL_EXTRACT_PATTERN.findall(text))
            if page_emails:
                emails.extend(
                    page_emails
                )  # Use extend to add, though it should be empty before
                logger.info(f"URL: {url} - Found emails on page: {emails}")
            else:
                logger.debug(f"URL: {url} - No valid emails found on page.")

        # Find RSS from page if not already found
        if not rss:
            link_tag = soup.find("link", {"type": "application/rss+xml", "href": True})
            if link_tag and link_tag.get("href") and is_valid_url(link_tag["href"]):
                href = link_tag["href"].strip()
                if looks_like_potential_rss(href):
                    rss = href
                    logger.info(f"URL: {url} - Found RSS feed via <link> tag: {rss}")

            if not rss:
                match = RSS_FIND_PATTERN.search(text)
                if match:
                    potential_rss = match.group(0).strip()
                    if is_valid_url(potential_rss):
                        rss = potential_rss
                        logger.info(
                            f"URL: {url} - Found potential RSS feed via text search: {rss}"
                        )

            # Final check if found RSS is a valid URL format
            if rss and not is_valid_url(rss):
                logger.warning(
                    "Ignoring invalid RSS URL format '%s' found on %s", rss, url
                )
                rss = None
    else:
        logger.info(
            f"URL: {url} - Skipping full page scrape as email and RSS found in description."
        )

    return {KEY_EMAILS: emails, KEY_RSS_URL: rss, KEY_TITLE: page_title}


# --- Spotify Fetching ---
def fetch_spotify_catalogue(
    limit_per_query: int = 50, max_offset: int = 1_000
) -> List[Dict[str, Any]]:
    queries = [
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
        "self-improvement",
    ]
    seen_ids: Set[str] = set()
    shows: List[Dict[str, Any]] = []
    api_call_delay = 0.5

    for q in queries:
        logger.info(f"Spotify: Searching for query '{q}'...")
        for offset in range(0, max_offset, limit_per_query):
            try:
                results = sp.search(
                    q=q, type="show", limit=limit_per_query, offset=offset
                )
                time.sleep(api_call_delay)
            except spotipy.SpotifyException as e:
                logger.error(f"Spotify API error for query '{q}' offset {offset}: {e}")
                sleep_time = api_call_delay
                if e.http_status == 429:
                    sleep_time = 60
                    logger.warning(
                        f"Rate limited by Spotify API. Sleeping for {sleep_time} seconds..."
                    )
                    time.sleep(sleep_time)
                    continue
                else:
                    time.sleep(sleep_time)
                    break
            except Exception as e:
                logger.error(
                    f"Unexpected error during Spotify search for '{q}': {e}",
                    exc_info=True,
                )
                time.sleep(api_call_delay)
                break

            items = results.get("shows", {}).get("items", [])
            if not items:
                logger.info(
                    f"Spotify: No more items for query '{q}' at offset {offset}."
                )
                break

            initial_count = len(shows)
            for item in items:
                if item["id"] not in seen_ids:
                    seen_ids.add(item["id"])
                    shows.append(
                        {
                            KEY_TITLE: item["name"],
                            KEY_SOURCE_URL: item["external_urls"]["spotify"],
                            KEY_PUBLISHER: item.get("publisher", ""),
                            KEY_RSS_URL: None,
                            KEY_EMAILS: [],
                            "description": item.get("description", ""),
                        }
                    )
            newly_added = len(shows) - initial_count
            logger.info(
                f"Spotify: Fetched {newly_added} new unique shows from this batch (Query: '{q}', Offset: {offset}). Total unique: {len(shows)}"
            )

    logger.info("Collected %d unique Spotify show URLs", len(shows))
    return shows


# --- Azure DB Fetching (Restored) ---
def fetch_data_from_azure_db(container_name, blob_path) -> List[Dict[str, Any]]:
    logger.info(
        f"Attempting to process database from Azure Blob: {container_name}/{blob_path}"
    )
    filtered_db_podcasts = []
    temp_db_path = None

    # Note: download_blob_to_tempfile now gets its own client
    temp_db_path = download_blob_to_tempfile(container_name, blob_path)
    if not temp_db_path:
        logger.warning("Failed to download Azure DB blob. Skipping Azure DB step.")
        return filtered_db_podcasts  # Return empty list

    conn = None
    try:
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        logger.info(f"Connected to temporary SQLite database: {temp_db_path}")

        # Query for entries with non-empty ownerEmail
        query = "SELECT title, url, author, ownerEmail FROM feeds WHERE ownerEmail IS NOT NULL AND ownerEmail != ''"
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info(f"Azure DB: Found {len(rows)} potential rows with email.")

        processed_count = 0
        skipped_count = 0

        for row in rows:
            title, feed_url, publisher, email_str = row

            # Validate URL
            feed_url = feed_url.strip() if feed_url else None
            is_feed_url_valid = is_valid_url(feed_url)

            # Validate Email using clean_emails
            cleaned_emails = clean_emails([email_str] if email_str else [])

            if cleaned_emails and is_feed_url_valid:
                filtered_db_podcasts.append(
                    {
                        KEY_TITLE: title.strip() if title else "",
                        KEY_RSS_URL: feed_url,
                        KEY_SOURCE_URL: feed_url,  # Use RSS as source URL for DB entries
                        KEY_PUBLISHER: publisher.strip() if publisher else "",
                        KEY_EMAILS: cleaned_emails,  # Use the cleaned list
                    }
                )
                processed_count += 1
            else:
                reason = []
                if not cleaned_emails:
                    reason.append("invalid/missing email")
                if not is_feed_url_valid:
                    reason.append("invalid/missing feed URL")
                logger.debug(
                    f"Skipping DB entry '{title}' due to: {', '.join(reason)}. Email='{email_str}', Feed='{feed_url}'"
                )
                skipped_count += 1

        logger.info(
            f"Azure DB: Processed {processed_count} valid entries, skipped {skipped_count}."
        )

    except sqlite3.Error as db_err:
        logger.error(
            f"Database error processing {temp_db_path}: {db_err}", exc_info=True
        )
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during DB processing: {e}", exc_info=True
        )
    finally:
        if conn:
            conn.close()
        if temp_db_path and os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
                logger.info(f"Removed temporary database file: {temp_db_path}")
            except OSError as remove_err:
                logger.error(
                    f"Error removing temporary file {temp_db_path}: {remove_err}"
                )

    logger.info(
        f"Returning {len(filtered_db_podcasts)} podcasts processed and filtered from the database."
    )
    return filtered_db_podcasts


# --- Podcast Index Fetching ---
def fetch_podcastindex_data(max_feeds=1000) -> List[Dict[str, Any]]:
    logger.info(
        f"Attempting to fetch up to {max_feeds} recent feeds from Podcast Index API..."
    )
    podcastindex_podcasts = []

    if not PODCASTINDEX_KEY or not PODCASTINDEX_SECRET:
        logger.error(
            "Podcast Index API Key or Secret not found in environment variables."
        )
        return podcastindex_podcasts

    api_header_time = str(int(time.time()))
    data_to_hash = PODCASTINDEX_KEY + PODCASTINDEX_SECRET + api_header_time
    sha1_hash = hashlib.sha1(data_to_hash.encode("utf-8")).hexdigest()
    headers = {
        "X-Auth-Date": api_header_time,
        "X-Auth-Key": PODCASTINDEX_KEY,
        "Authorization": sha1_hash,
        "User-Agent": "PodManager.ai/1.0",
    }
    api_url = (
        f"https://api.podcastindex.org/api/1.0/recent/feeds?max={max_feeds}&pretty"
    )

    try:
        session = requests_retry_session()
        response = session.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data.get("status") != "true":
            logger.error(
                f"Podcast Index API returned error status: {data.get('description', 'Unknown error')}"
            )
            return podcastindex_podcasts

        feeds = data.get("feeds", [])
        logger.info(f"Received {len(feeds)} feeds from Podcast Index API.")

        # Add counters for logging
        processed_count = 0
        skipped_email = 0
        skipped_rss = 0
        rss_fetch_attempts = 0
        rss_fetch_success_email = 0

        for feed in feeds:
            title = feed.get("title")
            rss_url = feed.get("url")
            email_str = feed.get("ownerEmail")  # Email from API
            publisher = feed.get("author")

            # Validate URL first
            rss_url = rss_url.strip() if rss_url else None
            is_feed_url_valid = is_valid_url(rss_url)

            # Validate Email from API data using clean_emails
            cleaned_emails = clean_emails([email_str] if email_str else [])

            # --- Fallback: Fetch RSS if email missing/invalid and URL is valid ---
            if not cleaned_emails and is_feed_url_valid:
                logger.info(
                    f"Podcast Index: Email missing/invalid for '{title}'. Attempting to fetch RSS feed: {rss_url}"
                )
                rss_fetch_attempts += 1
                # Use RSSService to fetch and parse the feed
                feed_data, status_code = RSSService.fetch_rss_feed(rss_url)
                if status_code == 200 and feed_data.get("email"):
                    rss_email = feed_data.get("email")
                    # Validate the email found via RSS fetch
                    rss_cleaned_emails = clean_emails([rss_email])
                    if rss_cleaned_emails:
                        logger.info(
                            f"Podcast Index: Found valid email '{rss_cleaned_emails[0]}' via RSS fetch for '{title}'."
                        )
                        cleaned_emails = rss_cleaned_emails  # Update cleaned_emails with the one found from RSS
                        rss_fetch_success_email += 1
                    else:
                        logger.info(
                            f"Podcast Index: Email '{rss_email}' found via RSS fetch for '{title}' was invalid after cleaning."
                        )
                else:
                    logger.info(
                        f"Podcast Index: Failed to fetch or find email in RSS feed for '{title}' (Status: {status_code})."
                    )
            # --- End Fallback ---

            # Final check: Do we have valid email(s) and a valid RSS URL?
            if cleaned_emails and is_feed_url_valid:
                podcastindex_podcasts.append(
                    {
                        KEY_TITLE: title.strip() if title else "",
                        KEY_RSS_URL: rss_url,
                        KEY_SOURCE_URL: rss_url,  # Use RSS as source URL
                        KEY_PUBLISHER: publisher.strip() if publisher else "",
                        KEY_EMAILS: cleaned_emails,  # Use the final list of cleaned emails
                    }
                )
                processed_count += 1
            else:
                # Log reason for skipping based on the final state
                reason = []
                # Check original email_str for logging context if fallback failed
                original_email_invalid = not clean_emails(
                    [email_str] if email_str else []
                )
                if original_email_invalid and not cleaned_emails:
                    reason.append("invalid/missing email (API & RSS fetch)")
                elif not cleaned_emails:
                    reason.append(
                        "invalid/missing email (API)"
                    )  # Should not happen if fallback works, but good to cover
                if not is_feed_url_valid:
                    reason.append("invalid/missing feed URL")

                logger.info(
                    f"Skipping Podcast Index entry '{title}' due to: {', '.join(reason)}. API Email='{email_str}', Feed='{rss_url}'"
                )
                # Count skips based on final state
                if not cleaned_emails:
                    skipped_email += 1
                if not is_feed_url_valid:
                    skipped_rss += 1

        # Update logging to include fetch attempts/successes
        logger.info(f"Podcast Index: Processed {processed_count} valid entries.")
        logger.info(
            f"Podcast Index: Attempted {rss_fetch_attempts} RSS fetches for missing emails, found {rss_fetch_success_email} valid emails."
        )
        logger.info(
            f"Podcast Index: Skipped {skipped_email} final entries for email, {skipped_rss} for RSS URL."
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Error during Podcast Index API request: {e}", exc_info=True)
    except Exception as e:
        logger.error(
            f"Unexpected error processing Podcast Index data: {e}", exc_info=True
        )  # Log full traceback

    logger.info(
        f"Returning {len(podcastindex_podcasts)} podcasts processed and filtered from Podcast Index."
    )
    return podcastindex_podcasts


# --- MongoDB Exclusion ---
def get_existing_user_podcast_rss_urls() -> Set[str]:
    existing_rss_urls = set()
    if not SCRAPE_DB_URI:
        logger.error(
            "SCRAPE_DB_URI not found in environment variables. Cannot check for existing user podcasts."
        )
        return existing_rss_urls

    try:
        parsed_uri = pymongo.uri_parser.parse_uri(SCRAPE_DB_URI)
        db_name = parsed_uri.get("database")
        if not db_name:
            db_name = "PodmanagerLive"
            logger.warning(
                f"Database name not found in SCRAPE_DB_URI, defaulting to '{db_name}'."
            )

        logger.info(f"Connecting to MongoDB '{db_name}' for exclusion check...")
        client = MongoClient(SCRAPE_DB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ismaster")
        db = client[db_name]
        users_collection = db["users"]

        pipeline = [
            {"$unwind": "$podcasts"},
            {"$match": {"podcasts.rss_url": {"$exists": True, "$ne": None, "$ne": ""}}},
            {"$group": {"_id": "$podcasts.rss_url"}},
        ]
        results = users_collection.aggregate(pipeline)

        for doc in results:
            existing_rss_urls.add(doc["_id"])

        logger.info(
            f"Found {len(existing_rss_urls)} unique RSS URLs associated with existing users."
        )
        client.close()

    except ConnectionFailure:
        logger.error(
            "MongoDB connection failed. Cannot check for existing user podcasts.",
            exc_info=True,
        )
    except ConfigurationError as ce:
        logger.error(
            f"MongoDB configuration error: {ce}. Cannot check for existing user podcasts.",
            exc_info=True,
        )
    except Exception as e:
        logger.error(
            f"Error fetching existing user podcast RSS URLs from MongoDB: {e}",
            exc_info=True,
        )

    return existing_rss_urls


# --- Caching Functions ---
def load_cache(cache_path):
    # Restore db_podcasts key
    default_data = {
        "filtered_spotify_podcasts": [],
        "filtered_podcastindex_podcasts": [],
        "filtered_db_podcasts": [],  # Re-add
    }
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all expected keys exist, provide defaults if missing
                final_data = {}
                for key in default_data:
                    final_data[key] = data.get(key, default_data[key])
                # Remove unexpected keys (optional, good practice)
                keys_to_remove = [k for k in data if k not in default_data]
                for k in keys_to_remove:
                    if k in final_data:  # Check if it exists before deleting
                        del final_data[k]
                logger.info(f"✅ Successfully loaded cache from {cache_path}")
                return final_data
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Cache file {cache_path} is corrupted. Starting fresh.")
            return default_data
        except IOError as e:
            logger.error(
                f"❌ Error reading cache file {cache_path}: {e}. Starting fresh."
            )
            return default_data
    else:
        logger.info("ℹ️ No cache file found. Starting fresh.")
        return default_data


def save_cache(cache_path, data):
    # Restore db_podcasts key
    expected_keys = {
        "filtered_spotify_podcasts",
        "filtered_podcastindex_podcasts",
        "filtered_db_podcasts",  # Re-add
    }
    data_to_save = {k: v for k, v in data.items() if k in expected_keys}
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2)
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
    filtered_podcastindex_podcasts = cached_data["filtered_podcastindex_podcasts"]
    filtered_db_podcasts = cached_data["filtered_db_podcasts"]  # Re-add

    # --- 1. Azure DB ---
    if not filtered_db_podcasts:
        logger.info("Fetching and filtering data from Azure DB...")
        filtered_db_podcasts = fetch_data_from_azure_db(AZURE_CONTAINER, AZURE_DB_BLOB)
        save_cache(
            CACHE_PATH,
            {
                "filtered_spotify_podcasts": filtered_spotify_podcasts,
                "filtered_podcastindex_podcasts": filtered_podcastindex_podcasts,
                "filtered_db_podcasts": filtered_db_podcasts,  # Save new
            },
        )
    else:
        logger.info("ℹ️ Skipping Azure DB fetching - data loaded from cache.")

    # --- 2. Podcast Index ---
    if not filtered_podcastindex_podcasts:
        logger.info("Fetching and filtering data from Podcast Index API...")
        filtered_podcastindex_podcasts = fetch_podcastindex_data(max_feeds=10000)
        save_cache(
            CACHE_PATH,
            {
                "filtered_spotify_podcasts": filtered_spotify_podcasts,
                "filtered_podcastindex_podcasts": filtered_podcastindex_podcasts,  # Save new
                "filtered_db_podcasts": filtered_db_podcasts,  # Keep existing
            },
        )
    else:
        logger.info("ℹ️ Skipping Podcast Index fetching - data loaded from cache.")

    # --- 3. Spotify Fetch & Scrape ---
    if not filtered_spotify_podcasts:
        logger.info("Fetching Spotify podcasts (Full Scrape)...")
        spotify_podcasts_raw = fetch_spotify_catalogue()
        logger.info(f"Fetched {len(spotify_podcasts_raw)} raw podcasts from Spotify.")

        processed_spotify_list = []
        logger.info(
            f"Processing Spotify podcasts: Scraping {len(spotify_podcasts_raw)} pages for emails/RSS and filtering..."
        )
        with ThreadPoolExecutor(max_workers=THREADS) as pool:
            # Pass description to scrape_page
            future_to_show = {
                pool.submit(scrape_page, s[KEY_SOURCE_URL], s.get("description")): s
                for s in spotify_podcasts_raw
            }
            processed_count = 0
            for future in as_completed(future_to_show):
                show_original = future_to_show[future]
                url = show_original[KEY_SOURCE_URL]
                processed_count += 1
                if processed_count % 100 == 0:
                    logger.info(
                        f"Spotify Scrape Progress: {processed_count}/{len(spotify_podcasts_raw)} pages processed."
                    )
                try:
                    scraped_data = future.result()
                    # Merge scraped data (emails, potentially RSS) into original show dict
                    # Use scraped emails directly as scrape_page now handles description + page
                    show_original[KEY_EMAILS] = scraped_data.get(KEY_EMAILS, [])
                    # Use scraped RSS directly
                    show_original[KEY_RSS_URL] = scraped_data.get(
                        KEY_RSS_URL
                    )  # Overwrite None if found

                    # --- Filter scraped Spotify shows ---
                    has_valid_email = bool(show_original[KEY_EMAILS])
                    has_valid_rss = is_valid_url(show_original.get(KEY_RSS_URL))

                    if has_valid_email and has_valid_rss:
                        show_original.pop(
                            "description", None
                        )  # Remove description before adding
                        processed_spotify_list.append(show_original)
                        logger.debug(
                            f"KEEPING Spotify podcast: '{show_original[KEY_TITLE]}' (Email: Yes, RSS: Yes)"
                        )
                    else:
                        # Log skips for Spotify items
                        reason = []
                        if not has_valid_email:
                            reason.append("no valid email found")
                        if not has_valid_rss:
                            reason.append("no valid RSS feed found")
                        logger.info(
                            f"SKIPPING Spotify podcast: '{show_original.get(KEY_TITLE, 'N/A')}' ({', '.join(reason)})"
                        )

                except Exception as exc:
                    logger.error(
                        f"Error processing result for {url}: {exc}", exc_info=True
                    )

        filtered_spotify_podcasts = processed_spotify_list
        logger.info(
            f"Found {len(filtered_spotify_podcasts)} Spotify podcasts meeting criteria (valid email & RSS)."
        )

        save_cache(
            CACHE_PATH,
            {
                "filtered_spotify_podcasts": filtered_spotify_podcasts,  # Save new
                "filtered_podcastindex_podcasts": filtered_podcastindex_podcasts,  # Keep existing
                "filtered_db_podcasts": filtered_db_podcasts,  # Keep existing
            },
        )
    else:
        logger.info("ℹ️ Skipping Spotify fetching/processing - data loaded from cache.")

    # --- 4. MongoDB Exclusion Check ---
    logger.info("Fetching existing user podcast associations from Live MongoDB...")
    existing_user_rss = get_existing_user_podcast_rss_urls()

    # --- 5. Combine, De-duplicate by RSS, and Clean ---
    logger.info("Combining and de-duplicating podcast data by RSS URL...")
    combined_data_by_rss: Dict[str, Dict[str, Any]] = {}
    duplicates_merged = 0

    # Re-add Azure DB to sources
    all_sources = [
        ("AzureDB", filtered_db_podcasts),
        ("PodcastIndex", filtered_podcastindex_podcasts),
        ("Spotify", filtered_spotify_podcasts),
    ]

    for source_name, source_data in all_sources:
        processed_count = 0
        for podcast in source_data:
            rss_url = podcast.get(KEY_RSS_URL)
            # Basic validation before using as key
            if not rss_url or not isinstance(rss_url, str) or not is_valid_url(rss_url):
                logger.warning(
                    f"Skipping item from {source_name} with invalid/missing RSS URL: {podcast.get(KEY_TITLE)} - {rss_url}"
                )
                continue

            # Ensure required fields exist, default to empty if not
            # Clean emails during this initial combination
            podcast_entry = {
                KEY_TITLE: podcast.get(KEY_TITLE, ""),
                KEY_RSS_URL: rss_url,
                KEY_EMAILS: clean_emails(
                    podcast.get(KEY_EMAILS, [])
                ),  # Clean emails here
                # Keep other fields temporarily if needed for XML, like publisher/source_url
                # KEY_PUBLISHER: podcast.get(KEY_PUBLISHER, ""),
                # KEY_SOURCE_URL: podcast.get(KEY_SOURCE_URL, "")
            }

            # Skip if no valid emails after cleaning
            if not podcast_entry[KEY_EMAILS]:
                logger.debug(
                    f"Skipping item from {source_name} with no valid emails after cleaning: {podcast.get(KEY_TITLE)}"
                )
                continue

            existing = combined_data_by_rss.get(rss_url)
            if not existing:
                combined_data_by_rss[rss_url] = podcast_entry
                processed_count += 1
            else:
                # Merge emails (already cleaned)
                new_emails = set(podcast_entry[KEY_EMAILS])
                existing_emails = set(existing[KEY_EMAILS])
                merged_emails = list(existing_emails.union(new_emails))
                if len(merged_emails) > len(existing_emails):
                    logger.debug(
                        f"Merging emails for duplicate RSS '{rss_url}' from {source_name}."
                    )
                    existing[KEY_EMAILS] = merged_emails
                    duplicates_merged += 1
                # Optionally merge/update title or other fields if desired

        logger.info(
            f"Processed {processed_count} unique items (by RSS) with valid emails from {source_name}."
        )

    if duplicates_merged > 0:
        logger.info(
            f"Merged email data for {duplicates_merged} duplicate podcasts found based on RSS URL."
        )

    logger.info(
        f"Total unique podcasts by RSS before exclusion: {len(combined_data_by_rss)}"
    )

    # --- 6. Exclude existing user feeds AND ensure email uniqueness ---
    logger.info(
        "Filtering combined data against existing users and ensuring email uniqueness..."
    )
    podcasts_for_xml = []
    seen_emails_in_final_list: Set[str] = set()  # Track emails added to the final list
    excluded_existing_user = 0
    excluded_duplicate_email = 0

    # Iterate through the combined data (keyed by RSS)
    for rss_url, podcast_data in combined_data_by_rss.items():
        # Check 1: Is it linked to an existing user?
        if rss_url in existing_user_rss:
            logger.debug(
                f"Excluding podcast '{podcast_data.get(KEY_TITLE)}' (RSS: {rss_url}) as it's linked to an existing user."
            )
            excluded_existing_user += 1
            continue

        # Check 2: Does it contain any email already added to the final list?
        current_podcast_emails = set(podcast_data.get(KEY_EMAILS, []))
        # Find intersection: emails in this podcast that are ALSO in seen_emails_in_final_list
        common_emails = current_podcast_emails.intersection(seen_emails_in_final_list)

        if common_emails:
            logger.info(
                f"Excluding podcast '{podcast_data.get(KEY_TITLE)}' (RSS: {rss_url}) due to duplicate email(s) already added: {common_emails}"
            )
            excluded_duplicate_email += 1
            continue

        # If checks pass, add to final list and update seen emails
        podcasts_for_xml.append(podcast_data)
        seen_emails_in_final_list.update(current_podcast_emails)

    logger.info(
        f"Excluded {excluded_existing_user} podcasts already associated with users."
    )
    logger.info(
        f"Excluded {excluded_duplicate_email} podcasts due to duplicate emails."
    )
    logger.info(
        f"Total unique podcasts for XML after all exclusions: {len(podcasts_for_xml)}"
    )

    # --- 7. Generate XML ---
    if podcasts_for_xml:
        logger.info("Generating XML file...")
        root = ET.Element("podcasts")

        for podcast in podcasts_for_xml:
            podcast_elem = ET.SubElement(root, "podcast")
            # Add only the required fields: title, rss, emails
            ET.SubElement(podcast_elem, KEY_TITLE).text = str(
                podcast.get(KEY_TITLE, "")
            )
            ET.SubElement(podcast_elem, KEY_RSS_URL).text = str(
                podcast.get(KEY_RSS_URL, "")
            )
            emails_elem = ET.SubElement(podcast_elem, KEY_EMAILS)
            for email in podcast.get(KEY_EMAILS, []):
                ET.SubElement(emails_elem, "email").text = email
            # Add the 'sent' status element, default to false
            ET.SubElement(podcast_elem, "sent").text = "false"

        # Pretty print XML
        xml_str = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        pretty_xml_str = dom.toprettyxml(indent="  ")

        output_filename = os.path.join(PROJECT_ROOT, "scraped.xml")

        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(pretty_xml_str)
            logger.info(f"✅ Podcast data successfully saved to {output_filename}")
            clear_cache(CACHE_PATH)
        except IOError as e:
            logger.error(f"❌ Error writing XML file: {e}", exc_info=True)
    else:
        logger.info("ℹ️ No podcasts meeting criteria found to save to XML.")
        clear_cache(CACHE_PATH)

    logger.info("--- Scraping Finished ---")
