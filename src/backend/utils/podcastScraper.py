from __future__ import annotations # Ensure this is the first line

import pymongo.uri_parser # For robust DB name parsing
import requests
import hashlib
import json # For caching
import logging
import os
import re
import sqlite3 # Re-add
import sys
import tempfile # Re-add
import time
import xml.etree.ElementTree as ET
import spotipy
from collections import Counter # Import Counter

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
# Use relative import for rss_Service
from ..services.rss_Service import RSSService

load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Constants ---
RSS_FIND_PATTERN = re.compile(r'https?://[^\s<>"\']+\.(?:rss|xml)\b|https?://[^\s<>"\']*(?:feed|rss)[^\s<>"\']*', re.IGNORECASE | re.UNICODE)
EMAIL_VALIDATE_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", re.UNICODE)
EMAIL_EXTRACT_PATTERN = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", re.UNICODE)

KEY_TITLE = "title"
KEY_RSS_URL = "rss"
KEY_SOURCE_URL = "url"
KEY_PUBLISHER = "publisher"
KEY_EMAILS = "emails"

# Add local DB path constant
LOCAL_DB_PATH = r"D:\Ploteye\scrapeDb\podcastindex_feeds.db" # Use raw string for Windows paths

# Add delay constant for Spotify API calls
SPOTIFY_API_DELAY_PER_REQUEST = 0.2 # Seconds to wait between API calls
SPOTIFY_API_DELAY_PER_QUERY = 1.0   # Seconds to wait between different search queries

# Add constants for Apple Podcasts (iTunes Search API)
APPLE_API_DELAY_PER_REQUEST = 1.0 # Delay for iTunes Search API
APPLE_API_BASE_URL = "https://itunes.apple.com/search"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
CACHE_PATH = os.path.join(PROJECT_ROOT, "scrape_cache.json") # Use consistent name

THREADS = int(os.getenv("SCRAPER_THREADS", "32"))

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

PODCASTINDEX_KEY = os.getenv("PODCAST_INDEX_KEY")
PODCASTINDEX_SECRET = os.getenv("PODCAST_INDEX_SECRET")
SCRAPE_DB_URI = os.getenv("SCRAPE_DB_URI")

# --- Session with Retries ---
def requests_retry_session(
    retries=5, # Slightly increase default retries
    backoff_factor=1.0,  # Default backoff for non-429 errors (e.g., sleep 0s, 2s, 4s, 8s, 16s)
    status_forcelist=(429, 500, 502, 503, 504), # Ensure 429 is included
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        respect_retry_after_header=True, # Add this to respect Retry-After header for 429s
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# --- Spotify Auth ---
# Create a session instance specifically for Spotify API calls
spotify_session = requests_retry_session()

try:
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-read-email",
            open_browser=True # Keep True if manual auth is needed first time
        ),
        requests_session=spotify_session, # Pass the custom session
        requests_timeout=15 # Set a default timeout for Spotify API calls
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
        potential_matches = EMAIL_EXTRACT_PATTERN.findall(raw)
        for potential in potential_matches:
            if EMAIL_VALIDATE_PATTERN.fullmatch(potential):
                seen.add(potential.lower())
    return list(seen)

def is_valid_url(url: str | None) -> bool:
    """Checks if a URL starts with http:// or https://."""
    return bool(url and url.lower().startswith(('http://', 'https://')))

# --- Local DB Fetching ---
def fetch_data_from_local_db(db_path: str, error_counter: Counter) -> List[Dict[str, Any]]:
    """
    Reads podcast data with emails directly from a local SQLite database file,
    attempting to dynamically determine table/column names, with fallbacks.
    """
    logger.info(f"Attempting to process database from local file: {db_path}")
    filtered_db_podcasts = []

    if not os.path.exists(db_path):
        logger.error(f"Local database file not found: {db_path}. Skipping local DB step.")
        error_counter["LocalDB: File Not Found"] += 1
        return filtered_db_podcasts

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        logger.info(f"Connected to local SQLite database: {db_path}")

        # --- Dynamically find table and columns ---
        table_name = None
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            if tables:
                table_name = tables[0][0] # Assume the first non-sqlite table is the one we want
                logger.info(f"Local DB: Found potential table: '{table_name}'")
            else:
                logger.error("Local DB: No user tables found in the database.")
                error_counter["LocalDB: No Tables Found"] += 1
                return filtered_db_podcasts
        except sqlite3.Error as e:
            logger.error(f"Local DB: Error querying sqlite_master: {e}", exc_info=True)
            error_counter["LocalDB: Schema Query Error"] += 1
            return filtered_db_podcasts

        column_map = {}
        actual_columns = []
        try:
            cursor.execute(f"PRAGMA table_info(\"{table_name}\");") # Quote table name
            columns_info = cursor.fetchall()
            actual_columns = [col[1].lower() for col in columns_info]
            logger.info(f"Local DB: Columns found in '{table_name}': {actual_columns}")

            # Define potential column names (lowercase), ordered by preference
            potential_names = {
                'title': ['title', 'podcasttitle', 'collectionname'],
                'url': ['url', 'feedurl', 'rssurl'],
                'originalurl': ['originalurl'], # Add originalurl for fallback
                'publisher': ['publisher', 'author', 'artistname', 'itunesauthor'],
                'email': ['owneremail', 'email', 'itunesowneremail', 'itunesownername'], # Prioritize owneremail
                'description': ['description', 'summary', 'itunessummary'] # For email fallback
            }

            required_fields = ['title', 'url', 'email'] # Need at least one URL source and one email source
            optional_fields = ['publisher', 'originalurl', 'description']
            found_columns = {}

            # Find required fields (title, at least one url, at least one email source)
            for field in ['title', 'url', 'email']: # Check core required fields first
                found = False
                # Special handling for email: prioritize owneremail
                candidates = potential_names[field]
                if field == 'email' and 'owneremail' in actual_columns:
                     candidates = ['owneremail'] + [c for c in candidates if c != 'owneremail']

                for potential in candidates:
                    if potential in actual_columns:
                        found_columns[field] = potential
                        found = True
                        logger.info(f"Local DB: Mapping required '{field}' to column '{potential}'")
                        break
                if not found:
                    # If 'url' not found, check if 'originalurl' exists before failing
                    if field == 'url' and any(p in actual_columns for p in potential_names['originalurl']):
                        logger.warning(f"Local DB: Primary URL column not found, will rely on originalurl.")
                    # If 'email' not found, check if 'description' exists before failing
                    elif field == 'email' and any(p in actual_columns for p in potential_names['description']):
                         logger.warning(f"Local DB: Primary email column not found, will rely on description parsing.")
                    else:
                        logger.error(f"Local DB: Could not find a suitable column for REQUIRED field '{field}' (or fallback). Searched: {potential_names[field]}")
                        error_counter[f"LocalDB: Missing Required Column For '{field}'"] += 1
                        return filtered_db_podcasts

            # Find optional fields (including fallbacks for url and email)
            for field in optional_fields:
                if field in found_columns: continue # Already mapped as required/primary
                found = False
                for potential in potential_names[field]:
                    if potential in actual_columns:
                        found_columns[field] = potential
                        found = True
                        logger.info(f"Local DB: Mapping optional/fallback '{field}' to column '{potential}'")
                        break
                if not found:
                    logger.warning(f"Local DB: Could not find a suitable column for optional/fallback field '{field}'. Searched: {potential_names[field]}")

            # Final check: Ensure we have at least one URL source and one email source mapped
            has_url_source = 'url' in found_columns or 'originalurl' in found_columns
            has_email_source = 'email' in found_columns or 'description' in found_columns
            if not has_url_source:
                 logger.error("Local DB: No URL source column (url or originalurl) could be mapped.")
                 error_counter["LocalDB: Missing URL Source"] += 1
                 return filtered_db_podcasts
            if not has_email_source:
                 logger.error("Local DB: No email source column (email candidates or description) could be mapped.")
                 error_counter["LocalDB: Missing Email Source"] += 1
                 return filtered_db_podcasts

            column_map = found_columns

        except sqlite3.Error as e:
            logger.error(f"Local DB: Error inspecting schema for '{table_name}': {e}", exc_info=True)
            error_counter["LocalDB: Schema Query Error"] += 1
            return filtered_db_podcasts
        # --- End Dynamic Find ---


        # --- Build and Execute Dynamic Query ---
        # Select all mapped columns to simplify indexing
        select_columns_ordered = list(column_map.keys()) # Get the fields we mapped (e.g., 'title', 'url', 'email', 'originalurl')
        select_clause_cols = [column_map[field] for field in select_columns_ordered] # Get the actual DB column names

        select_clause = ", ".join(f'"{col}"' for col in select_clause_cols)
        query = f"SELECT {select_clause} FROM \"{table_name}\""

        logger.info(f"Local DB: Executing dynamic query: {query}")
        cursor.execute(query)
        logger.info(f"Local DB: Fetching rows...")

        processed_count = 0
        skipped_count = 0
        fetched_count = 0

        while True:
            rows_batch = cursor.fetchmany(10000) # Process in batches
            if not rows_batch:
                break
            fetched_count += len(rows_batch)

            for row in rows_batch:
                row_data = {field: row[idx] for idx, field in enumerate(select_columns_ordered)}

                title = row_data.get('title', "")
                publisher = row_data.get('publisher', "") # Will be None if not mapped
                email_str = row_data.get('email', "") # Primary email source
                description_str = row_data.get('description', "") # Fallback email source
                url_str = row_data.get('url', "") # Primary URL source
                originalurl_str = row_data.get('originalurl', "") # Fallback URL source

                # --- URL Validation with Fallback ---
                feed_url = None
                url_source_column = None
                if is_valid_url(url_str):
                    feed_url = url_str.strip()
                    url_source_column = column_map.get('url', 'url') # Log which column worked
                elif 'originalurl' in column_map and is_valid_url(originalurl_str):
                    feed_url = originalurl_str.strip()
                    url_source_column = column_map.get('originalurl', 'originalurl')
                    logger.debug(f"Using fallback URL from '{url_source_column}' for '{title}': {feed_url}")
                # --- End URL Validation ---

                # --- Email Validation with Fallback ---
                cleaned_emails = []
                email_source_info = "N/A"
                # 1. Try primary email column
                if email_str:
                    cleaned_emails = clean_emails([email_str])
                    if cleaned_emails:
                        email_source_info = f"column '{column_map.get('email', 'email')}' ('{email_str}')"

                # 2. If primary failed, try parsing description (if available)
                if not cleaned_emails and description_str and 'description' in column_map:
                    logger.debug(f"Attempting email extraction from description for '{title}'")
                    potential_emails_in_desc = EMAIL_EXTRACT_PATTERN.findall(description_str)
                    if potential_emails_in_desc:
                        cleaned_emails = clean_emails(potential_emails_in_desc) # Validate extracted emails
                        if cleaned_emails:
                             email_source_info = f"description parsing ('{cleaned_emails[0]}'...)"
                             logger.debug(f"Found email via description parsing for '{title}': {cleaned_emails}")

                # --- End Email Validation ---

                # --- Final Check and Append/Skip ---
                is_feed_url_valid = bool(feed_url) # Check if we found a valid URL

                if cleaned_emails and is_feed_url_valid:
                    filtered_db_podcasts.append({
                        KEY_TITLE: title.strip() if title else "",
                        KEY_RSS_URL: feed_url,
                        KEY_SOURCE_URL: feed_url,
                        KEY_PUBLISHER: publisher.strip() if publisher else "",
                        KEY_EMAILS: cleaned_emails
                    })
                    processed_count += 1
                else:
                    skipped_count += 1
                    reason = []
                    if not cleaned_emails:
                         reason.append(f"invalid/missing email (tried: {email_source_info})")
                    if not is_feed_url_valid:
                         url_val = url_str if url_str else "N/A"
                         orig_url_val = originalurl_str if originalurl_str else "N/A"
                         reason.append(f"invalid/missing feed URL (url='{url_val}', originalurl='{orig_url_val}')")
                    logger.debug(f"Skipping DB entry '{title}' due to: {', '.join(reason)}")
            if fetched_count % 100000 == 0:
                 logger.info(f"Local DB: Fetched {fetched_count} rows...")

        logger.info(f"Local DB: Finished fetching {fetched_count} total rows.")
        logger.info(f"Local DB: Processed {processed_count} valid entries, skipped {skipped_count}.")

    except sqlite3.OperationalError as op_err:
        logger.error(f"Database operational error processing {db_path}: {op_err}", exc_info=True)
        error_counter["LocalDB: Operational Error"] += 1
    except sqlite3.DatabaseError as db_err:
        logger.error(f"Database error processing {db_path}: {db_err}", exc_info=True)
        error_counter["LocalDB: Database Error"] += 1
    except sqlite3.Error as db_err:
        logger.error(f"SQLite error processing {db_path}: {db_err}", exc_info=True)
        error_counter["LocalDB: SQLite Error"] += 1
    except Exception as e:
        logger.error(f"An unexpected error occurred during local DB processing: {e}", exc_info=True)
        error_counter["LocalDB: Unexpected Processing Error"] += 1
    finally:
        if conn:
            conn.close()
            logger.info(f"Closed connection to local database: {db_path}")

    logger.info(f"Returning {len(filtered_db_podcasts)} podcasts processed and filtered from the local database.")
    return filtered_db_podcasts

# --- Podcast Index Fetching ---
def fetch_podcastindex_data(error_counter: Counter, max_feeds=1000) -> List[Dict[str, Any]]:
    """Fetches recent podcast feeds from the Podcast Index API and filters them."""
    logger.info(f"Attempting to fetch up to {max_feeds} recent feeds from Podcast Index API...")
    podcastindex_podcasts = []

    if not PODCASTINDEX_KEY or not PODCASTINDEX_SECRET:
        logger.error("Podcast Index API Key or Secret not found in environment variables.")
        error_counter["PodcastIndex: Missing Credentials"] += 1
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
        session = requests_retry_session()
        response = session.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data.get('status') != 'true':
            error_desc = data.get('description', 'Unknown API error')
            logger.error(f"Podcast Index API returned error status: {error_desc}")
            error_counter[f"PodcastIndex: API Status Error - {error_desc[:50]}"] += 1
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
            email_str = feed.get('ownerEmail') # Email from API
            publisher = feed.get('author')

            rss_url = rss_url.strip() if rss_url else None
            is_feed_url_valid = is_valid_url(rss_url)

            cleaned_emails = clean_emails([email_str] if email_str else [])

            # --- Fallback: Fetch RSS if email missing/invalid and URL is valid ---
            if not cleaned_emails and is_feed_url_valid:
                logger.info(f"Podcast Index: Email missing/invalid for '{title}'. Attempting to fetch RSS feed: {rss_url}")
                rss_fetch_attempts += 1
                try:
                    feed_data, status_code = RSSService.fetch_rss_feed(rss_url)
                    if status_code == 200 and feed_data.get("email"):
                        rss_email = feed_data.get("email")
                        rss_cleaned_emails = clean_emails([rss_email])
                        if rss_cleaned_emails:
                            logger.info(f"Podcast Index: Found valid email '{rss_cleaned_emails[0]}' via RSS fetch for '{title}'.")
                            cleaned_emails = rss_cleaned_emails
                            rss_fetch_success_email += 1
                        else:
                            logger.info(f"Podcast Index: Email '{rss_email}' found via RSS fetch for '{title}' was invalid after cleaning.")
                    elif status_code != 200:
                         logger.info(f"Podcast Index: Failed to fetch RSS feed for '{title}' (Status: {status_code}).")
                         error_counter[f"PodcastIndex: RSS Fallback HTTP Error {status_code}"] += 1
                    else:
                         logger.info(f"Podcast Index: Fetched RSS feed for '{title}' but no email found.")
                except Exception as rss_exc:
                    logger.error(f"Podcast Index: Error during RSS fallback fetch for '{title}' ({rss_url}): {rss_exc}", exc_info=False)
                    error_counter["PodcastIndex: RSS Fallback Exception"] += 1
            # --- End Fallback ---

            if cleaned_emails and is_feed_url_valid:
                podcastindex_podcasts.append({
                    KEY_TITLE: title.strip() if title else "",
                    KEY_RSS_URL: rss_url,
                    KEY_SOURCE_URL: rss_url,
                    KEY_PUBLISHER: publisher.strip() if publisher else "",
                    KEY_EMAILS: cleaned_emails
                })
                processed_count += 1
            else:
                reason = []
                original_email_invalid = not clean_emails([email_str] if email_str else [])
                if original_email_invalid and not cleaned_emails: reason.append("invalid/missing email (API & RSS fetch)")
                elif not cleaned_emails: reason.append("invalid/missing email (API)")
                if not is_feed_url_valid: reason.append("invalid/missing feed URL")

                logger.info(f"Skipping Podcast Index entry '{title}' due to: {', '.join(reason)}. API Email='{email_str}', Feed='{rss_url}'")
                if not cleaned_emails: skipped_email += 1
                if not is_feed_url_valid: skipped_rss += 1

        logger.info(f"Podcast Index: Processed {processed_count} valid entries.")
        logger.info(f"Podcast Index: Attempted {rss_fetch_attempts} RSS fetches for missing emails, found {rss_fetch_success_email} valid emails.")
        logger.info(f"Podcast Index: Skipped {skipped_email} final entries for email, {skipped_rss} for RSS URL.")

    except requests.exceptions.Timeout:
        logger.error(f"Timeout during Podcast Index API request: {api_url}", exc_info=True)
        error_counter["PodcastIndex: API Request Timeout"] += 1
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during Podcast Index API request: {e}", exc_info=True)
        error_counter["PodcastIndex: API Request Error"] += 1
    except Exception as e:
        logger.error(f"Unexpected error processing Podcast Index data: {e}", exc_info=True)
        error_counter["PodcastIndex: Unexpected Processing Error"] += 1

    logger.info(f"Returning {len(podcastindex_podcasts)} podcasts processed and filtered from Podcast Index.")
    return podcastindex_podcasts

# --- Apple Podcasts (iTunes Search API) Fetching ---
def fetch_apple_podcasts_data(error_counter: Counter, limit_per_query: int = 200) -> List[Dict[str, Any]]:
    """Fetches podcast data from the iTunes Search API."""
    logger.info("Attempting to fetch data from Apple Podcasts (via iTunes Search API)...")
    apple_podcasts = []

    # Use similar queries as Spotify
    queries = [
        "podcast", "news podcast", "music podcast", "tech podcast", "sports podcast",
        "health podcast", "comedy podcast", "business podcast", "education podcast",
        "science podcast", "history podcast", "true crime podcast", "interview",
        "storytelling", "technology", "finance", "politics", "culture", "arts",
        "self-improvement"
    ]
    session = requests_retry_session()
    seen_rss: Set[str] = set() # Track RSS URLs to avoid duplicates

    for q_index, q in enumerate(queries):
        logger.info(f"Apple Podcasts: Searching for query '{q}' ({q_index + 1}/{len(queries)})...")
        processed_for_query = 0
        skipped_email_for_query = 0
        skipped_rss_for_query = 0
        rss_fetch_attempts_for_query = 0
        rss_fetch_success_email_for_query = 0

        params = {
            'term': q,
            'media': 'podcast',
            'entity': 'podcast',
            'limit': limit_per_query, # Max 200 for iTunes Search API
            'country': 'US' # Optional: Specify country for relevance
        }
        api_url = APPLE_API_BASE_URL

        try:
            # Add delay before each request
            logger.debug(f"Waiting {APPLE_API_DELAY_PER_REQUEST}s before Apple API call (Query: '{q}')...")
            time.sleep(APPLE_API_DELAY_PER_REQUEST)

            response = session.get(api_url, params=params, timeout=25) # Slightly longer timeout
            response.raise_for_status() # Will trigger retry logic for 429, 5xx

            data = response.json()
            results = data.get('results', [])

            logger.info(f"Apple Podcasts: Received {len(results)} results for query '{q}'.")

            for item in results:
                title = item.get('collectionName')
                rss_url = item.get('feedUrl')
                publisher = item.get('artistName')
                source_url = item.get('collectionViewUrl') # Link to the podcast on Apple Podcasts

                # Basic validation
                rss_url = rss_url.strip() if rss_url else None
                is_feed_url_valid = is_valid_url(rss_url)

                # Skip if RSS already seen or invalid
                if not is_feed_url_valid:
                    logger.debug(f"Apple Podcasts: Skipping '{title}' due to invalid/missing RSS URL: {rss_url}")
                    skipped_rss_for_query += 1
                    continue
                if rss_url in seen_rss:
                    logger.debug(f"Apple Podcasts: Skipping '{title}' as RSS URL '{rss_url}' already processed.")
                    continue

                # iTunes API doesn't provide email, so we always need to fetch RSS
                cleaned_emails = []
                logger.info(f"Apple Podcasts: Attempting to fetch RSS feed for email: {rss_url}")
                rss_fetch_attempts_for_query += 1
                try:
                    feed_data, status_code = RSSService.fetch_rss_feed(rss_url)
                    if status_code == 200 and feed_data.get("email"):
                        rss_email = feed_data.get("email")
                        rss_cleaned_emails = clean_emails([rss_email])
                        if rss_cleaned_emails:
                            logger.info(f"Apple Podcasts: Found valid email '{rss_cleaned_emails[0]}' via RSS fetch for '{title}'.")
                            cleaned_emails = rss_cleaned_emails
                            rss_fetch_success_email_for_query += 1
                        else:
                            logger.info(f"Apple Podcasts: Email '{rss_email}' found via RSS fetch for '{title}' was invalid.")
                    elif status_code != 200:
                        logger.info(f"Apple Podcasts: Failed to fetch RSS feed for '{title}' (Status: {status_code}).")
                        error_counter[f"ApplePodcasts: RSS Fallback HTTP Error {status_code}"] += 1
                    else:
                        logger.info(f"Apple Podcasts: Fetched RSS feed for '{title}' but no email found.")
                except Exception as rss_exc:
                    logger.error(f"Apple Podcasts: Error during RSS fallback fetch for '{title}' ({rss_url}): {rss_exc}", exc_info=False)
                    error_counter["ApplePodcasts: RSS Fallback Exception"] += 1

                # Final check: Do we have valid email(s) and a valid RSS URL?
                if cleaned_emails and is_feed_url_valid:
                    apple_podcasts.append({
                        KEY_TITLE: title.strip() if title else "",
                        KEY_RSS_URL: rss_url,
                        KEY_SOURCE_URL: source_url or rss_url, # Prefer Apple Podcasts URL if available
                        KEY_PUBLISHER: publisher.strip() if publisher else "",
                        KEY_EMAILS: cleaned_emails
                    })
                    seen_rss.add(rss_url) # Mark RSS as processed
                    processed_for_query += 1
                else:
                    # Log reason for skipping
                    reason = []
                    if not cleaned_emails: reason.append("invalid/missing email (RSS fetch)")
                    # We already skipped invalid RSS URLs earlier
                    logger.info(f"Skipping Apple Podcasts entry '{title}' due to: {', '.join(reason)}. Feed='{rss_url}'")
                    if not cleaned_emails: skipped_email_for_query += 1
                    # Don't add to seen_rss if skipped

        except requests.exceptions.Timeout:
            logger.error(f"Timeout during Apple Podcasts API request for query '{q}'.", exc_info=True)
            error_counter["ApplePodcasts: API Request Timeout"] += 1
            continue # Continue to the next query on timeout
        except requests.exceptions.HTTPError as e:
             status_code = e.response.status_code
             logger.error(f"HTTP error {status_code} during Apple Podcasts API request for query '{q}': {e}", exc_info=False)
             error_counter[f"ApplePodcasts: API HTTP Error {status_code}"] += 1
             continue # Continue to the next query
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception during Apple Podcasts API request for query '{q}': {e}", exc_info=True)
            error_counter["ApplePodcasts: API Request Exception"] += 1
            continue # Continue to the next query
        except Exception as e:
            logger.error(f"Unexpected error processing Apple Podcasts data for query '{q}': {e}", exc_info=True)
            error_counter["ApplePodcasts: Unexpected Processing Error"] += 1
            continue # Continue to the next query

        # Log summary for the query
        logger.info(f"Apple Podcasts Query '{q}' Summary: Processed={processed_for_query}, SkippedEmail={skipped_email_for_query}, SkippedRSS={skipped_rss_for_query}, RSSFallbacks={rss_fetch_attempts_for_query}, RSSSuccess={rss_fetch_success_email_for_query}")

    logger.info(f"Returning {len(apple_podcasts)} podcasts processed and filtered from Apple Podcasts.")
    return apple_podcasts

# --- Caching Functions ---
def load_cache(cache_path):
    """Loads cached data from a JSON file."""
    default_data = {
        "filtered_spotify_podcasts": [],
        "filtered_podcastindex_podcasts": [],
        "filtered_db_podcasts": [],
        "filtered_apple_podcasts": [],
    }
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure all expected keys exist, provide defaults if missing
                final_data = {}
                for key in default_data:
                    final_data[key] = data.get(key, default_data[key])
                logger.info(f"✅ Successfully loaded cache from {cache_path}")
                return final_data
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
    """Saves data to a JSON cache file."""
    expected_keys = {
        "filtered_spotify_podcasts",
        "filtered_podcastindex_podcasts",
        "filtered_db_podcasts",
        "filtered_apple_podcasts",
    }
    data_to_save = {k: v for k, v in data.items() if k in expected_keys}
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2)
        logger.info(f"✅ Progress saved to cache file: {cache_path}")
    except IOError as e:
        logger.error(f"❌ Error writing cache file {cache_path}: {e}")
    except TypeError as e:
        logger.error(f"❌ Error serializing data for cache: {e}")

# --- Placeholder Functions (Define properly elsewhere if needed) ---
def get_existing_user_podcast_rss_urls() -> Set[str]:
    """Placeholder: Returns a set of RSS URLs associated with existing users."""
    logger.warning("Using placeholder function for get_existing_user_podcast_rss_urls. Define properly if needed.")
    # Example: Connect to your user database and retrieve RSS feeds
    # For now, return an empty set
    return set()

def clear_cache(cache_path: str):
    """Placeholder: Clears the cache file."""
    logger.warning(f"Using placeholder function for clear_cache({cache_path}). Define properly if needed.")
    try:
        if os.path.exists(cache_path):
            os.remove(cache_path)
            logger.info(f"Placeholder: Cleared cache file {cache_path}")
    except Exception as e:
        logger.error(f"Placeholder: Error clearing cache {cache_path}: {e}")
# --- End Placeholder Functions ---


# --- Main Execution ---
if __name__ == "__main__":
    logger.info("--- Starting Podcast Scraping ---")
    error_summary_counter = Counter() # Initialize the counter

    # --- Load Cache ---
    logger.info("Step 1: Loading cache...")
    cached_data = load_cache(CACHE_PATH)
    filtered_spotify_podcasts = cached_data["filtered_spotify_podcasts"]
    filtered_podcastindex_podcasts = cached_data["filtered_podcastindex_podcasts"]
    filtered_db_podcasts = cached_data["filtered_db_podcasts"]
    filtered_apple_podcasts = cached_data["filtered_apple_podcasts"] # Load Apple cache
    logger.info("Step 1: Cache loaded.")
    logger.info(f" > Cached DB podcasts: {len(filtered_db_podcasts)}")
    logger.info(f" > Cached PodcastIndex podcasts: {len(filtered_podcastindex_podcasts)}")
    logger.info(f" > Cached Apple podcasts: {len(filtered_apple_podcasts)}")
    logger.info(f" > Cached Spotify podcasts: {len(filtered_spotify_podcasts)}")


    # --- 1. Local DB ---
    logger.info("Step 2: Checking Local DB data...")
    if not filtered_db_podcasts:
        logger.info(" > Cache empty. Fetching and filtering data from Local DB...")
        filtered_db_podcasts = fetch_data_from_local_db(LOCAL_DB_PATH, error_summary_counter)
        cached_data["filtered_db_podcasts"] = filtered_db_podcasts
        save_cache(CACHE_PATH, cached_data)
        logger.info(" > Local DB fetching complete.")
    else:
        logger.info(" > Skipping Local DB fetching - data loaded from cache.")
    logger.info("Step 2: Local DB check complete.")

    # --- 2. Podcast Index ---
    logger.info("Step 3: Checking Podcast Index data...")
    if not filtered_podcastindex_podcasts:
        logger.info(" > Cache empty. Fetching and filtering data from Podcast Index API...")
        filtered_podcastindex_podcasts = fetch_podcastindex_data(error_summary_counter, max_feeds=10000) # Reduced max_feeds for testing if needed
        cached_data["filtered_podcastindex_podcasts"] = filtered_podcastindex_podcasts
        save_cache(CACHE_PATH, cached_data)
        logger.info(" > Podcast Index fetching complete.")
    else:
        logger.info(" > Skipping Podcast Index fetching - data loaded from cache.")
    logger.info("Step 3: Podcast Index check complete.")

    # --- 3. Apple Podcasts ---
    logger.info("Step 4: Checking Apple Podcasts data...")
    if not filtered_apple_podcasts:
        logger.info(" > Cache empty. Fetching and filtering data from Apple Podcasts (iTunes Search API)...")
        filtered_apple_podcasts = fetch_apple_podcasts_data(error_summary_counter)
        cached_data["filtered_apple_podcasts"] = filtered_apple_podcasts
        save_cache(CACHE_PATH, cached_data)
        logger.info(" > Apple Podcasts fetching complete.")
    else:
        logger.info(" > Skipping Apple Podcasts fetching - data loaded from cache.")
    logger.info("Step 4: Apple Podcasts check complete.")

    # --- 4. Spotify Fetch & Process ---
    logger.info("Step 5: Checking Spotify data...")
    if not filtered_spotify_podcasts:
        logger.info(" > Cache empty. Fetching Spotify podcasts...")
        # Add your Spotify fetching logic call here if it exists
        # Example: filtered_spotify_podcasts = fetch_spotify_data(error_summary_counter)
        logger.warning(" > Spotify fetching logic not implemented in main block yet.") # Placeholder warning
        # Assuming Spotify logic populates filtered_spotify_podcasts
        cached_data["filtered_spotify_podcasts"] = filtered_spotify_podcasts
        save_cache(CACHE_PATH, cached_data)
        logger.info(" > Spotify fetching complete.")
    else:
        logger.info(" > Skipping Spotify fetching/processing - data loaded from cache.")
    logger.info("Step 5: Spotify check complete.")

    # --- Combine, De-duplicate by RSS, and Clean ---
    logger.info("Step 6: Combining and de-duplicating podcast data...")
    combined_data_by_rss: Dict[str, Dict[str, Any]] = {}
    duplicates_merged = 0

    # Add ApplePodcasts to the sources
    all_sources = [
        ("LocalDB", filtered_db_podcasts),
        ("PodcastIndex", filtered_podcastindex_podcasts),
        ("ApplePodcasts", filtered_apple_podcasts), # Add ApplePodcasts
        ("Spotify", filtered_spotify_podcasts),
    ]

    for source_name, source_data in all_sources:
        # ... (inner loop remains the same) ...
        processed_count = 0
        for podcast in source_data:
            rss_url = podcast.get(KEY_RSS_URL)
            if not rss_url or not isinstance(rss_url, str) or not is_valid_url(rss_url):
                logger.warning(f"Skipping item from {source_name} with invalid/missing RSS URL: {podcast.get(KEY_TITLE)} - {rss_url}")
                continue

            podcast_entry = {
                KEY_TITLE: podcast.get(KEY_TITLE, ""),
                KEY_RSS_URL: rss_url,
                KEY_EMAILS: clean_emails(podcast.get(KEY_EMAILS, []))
            }

            if not podcast_entry[KEY_EMAILS]:
                logger.debug(f"Skipping item from {source_name} with no valid emails after cleaning: {podcast.get(KEY_TITLE)}")
                continue

            existing = combined_data_by_rss.get(rss_url)
            if not existing:
                combined_data_by_rss[rss_url] = podcast_entry
                processed_count += 1
            else:
                new_emails = set(podcast_entry[KEY_EMAILS])
                existing_emails = set(existing[KEY_EMAILS])
                merged_emails = list(existing_emails.union(new_emails))
                if len(merged_emails) > len(existing_emails):
                    logger.debug(f"Merging emails for duplicate RSS '{rss_url}' from {source_name}.")
                    existing[KEY_EMAILS] = merged_emails
                    duplicates_merged += 1

        logger.info(f" > Processed {processed_count} unique items (by RSS) with valid emails from {source_name}.")


    if duplicates_merged > 0:
        logger.info(f" > Merged email data for {duplicates_merged} duplicate podcasts found based on RSS URL.")

    logger.info(f" > Total unique podcasts by RSS before exclusion: {len(combined_data_by_rss)}")
    candidate_podcast_count = len(combined_data_by_rss)
    logger.info("Step 6: Combining and de-duplication complete.")

    # --- Exclude existing user feeds AND ensure email uniqueness ---
    logger.info("Step 7: Filtering combined data...")
    podcasts_for_xml = []
    seen_emails_in_final_list: Set[str] = set()
    excluded_existing_user = 0
    excluded_duplicate_email = 0

    # Fetch existing user RSS URLs (using placeholder)
    existing_user_rss = get_existing_user_podcast_rss_urls()
    logger.info(f" > Found {len(existing_user_rss)} existing user RSS URLs to exclude.")

    for rss_url, podcast_data in combined_data_by_rss.items():
        if rss_url in existing_user_rss: # Use the fetched set
            logger.debug(f"Excluding podcast '{podcast_data.get(KEY_TITLE)}' (RSS: {rss_url}) as it's linked to an existing user.")
            excluded_existing_user += 1
            continue

        # ... (rest of the loop remains the same) ...
        current_podcast_emails = set(podcast_data.get(KEY_EMAILS, []))
        common_emails = current_podcast_emails.intersection(seen_emails_in_final_list)

        if common_emails:
            logger.info(f"Excluding podcast '{podcast_data.get(KEY_TITLE)}' (RSS: {rss_url}) due to duplicate email(s) already added: {common_emails}")
            excluded_duplicate_email += 1
            continue

        podcasts_for_xml.append(podcast_data)
        seen_emails_in_final_list.update(current_podcast_emails)


    logger.info(f" > Excluded {excluded_existing_user} podcasts already associated with users.")
    logger.info(f" > Excluded {excluded_duplicate_email} podcasts due to duplicate emails.")
    logger.info(f" > Total unique podcasts for XML after all exclusions: {len(podcasts_for_xml)}")
    final_xml_podcast_count = len(podcasts_for_xml)
    logger.info("Step 7: Filtering complete.")

    # --- Generate XML ---
    logger.info("Step 8: Generating XML...")
    if podcasts_for_xml:
        # ... (XML generation logic remains the same) ...
        logger.info(" > Generating XML file...")
        root = ET.Element("podcasts")

        for podcast in podcasts_for_xml:
            podcast_elem = ET.SubElement(root, "podcast")
            ET.SubElement(podcast_elem, KEY_TITLE).text = str(podcast.get(KEY_TITLE, ""))
            ET.SubElement(podcast_elem, KEY_RSS_URL).text = str(podcast.get(KEY_RSS_URL, ""))
            emails_elem = ET.SubElement(podcast_elem, KEY_EMAILS)
            for email in podcast.get(KEY_EMAILS, []):
                ET.SubElement(emails_elem, "email").text = str(email)

        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml_str = dom.toprettyxml(indent="  ")

        output_filename = os.path.join(PROJECT_ROOT, "scraped.xml")

        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(pretty_xml_str)
            logger.info(f" > ✅ Podcast data successfully saved to {output_filename}")
            clear_cache(CACHE_PATH) # Call placeholder clear_cache
        except IOError as e:
            logger.error(f" > ❌ Error writing XML file: {e}", exc_info=True)
    else:
        logger.info(" > ℹ️ No podcasts meeting criteria found to save to XML.")
        clear_cache(CACHE_PATH) # Call placeholder clear_cache
    logger.info("Step 8: XML Generation complete.")


    logger.info("--- Scraping Finished ---")
