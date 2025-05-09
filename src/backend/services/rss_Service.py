import requests
import xml.etree.ElementTree as ET
import logging
import feedparser
from datetime import datetime, timezone
import re
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

# Define ITMS_NS for iTunes specific tags
ITMS_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"

class RSSService:
    def _ensure_utc(self, dt_obj):
        """
        Ensures the datetime object is timezone-aware and in UTC.
        Converts time.struct_time to datetime object if necessary.
        Returns a datetime.datetime object or None.
        """
        if dt_obj is None:
            return None

        # Convert time.struct_time to datetime object if necessary
        if isinstance(dt_obj, time.struct_time):
            try:
                dt_obj = datetime.fromtimestamp(time.mktime(dt_obj))
            except OverflowError:
                logger.warning(f"Could not convert time.struct_time to datetime due to OverflowError: {dt_obj}")
                return None

        if not isinstance(dt_obj, datetime):
            logger.warning(f"Unexpected type for dt_obj in _ensure_utc: {type(dt_obj)}. Expected datetime or time.struct_time.")
            return None

        if dt_obj.tzinfo is None:
            return dt_obj.replace(tzinfo=timezone.utc)
        return dt_obj.astimezone(timezone.utc)

    def _sanitize_html(self, html_content):
        if not html_content:
            return None
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text()

    def _parse_duration(self, duration_str):
        if not duration_str:
            return None
        try:
            if ':' in duration_str:
                parts = list(map(int, duration_str.split(':')))
                if len(parts) == 3:  # HH:MM:SS
                    return parts[0] * 3600 + parts[1] * 60 + parts[2]
                elif len(parts) == 2:  # MM:SS
                    return parts[0] * 60 + parts[1]
            return int(duration_str)  # Assume it's in seconds
        except ValueError:
            return None

    def parse_rss_data(self, feed_content, feed_url):
        try:
            feed = feedparser.parse(feed_content)
            logger.info(f"Feedparser parsed feed for URL: {feed_url}. Feed title: {feed.feed.get('title', 'N/A')}")
            logger.info(f"Number of entries found by feedparser: {len(feed.entries)}")

            if feed.bozo:
                bozo_exception_type = type(feed.bozo_exception).__name__
                logger.warning(
                    f"⚠️ RSS feed at {feed_url} is not well-formed (bozo). Exception: {bozo_exception_type} - {str(feed.bozo_exception)}"
                )

            feed_last_build_date_obj = self._ensure_utc(feed.feed.get("updated_parsed") or feed.feed.get("published_parsed"))

            parsed_data = {
                "title": feed.feed.get("title"),
                "description": self._sanitize_html(feed.feed.get("description") or feed.feed.get("subtitle")),
                "imageUrl": feed.feed.get("image", {}).get("href") if feed.feed.get("image") else None,
                "feedUrl": feed_url,
                "link": feed.feed.get("link"),
                "language": feed.feed.get("language"),
                "copyright_info": feed.feed.get("rights") or feed.feed.get("copyright"),
                "lastBuildDate": feed_last_build_date_obj.isoformat() if feed_last_build_date_obj else None,
                "generator": feed.feed.get("generator"),
                "author": feed.feed.get("author_detail", {}).get("name") if feed.feed.get("author_detail") else feed.feed.get("author"),
                "itunesOwner": {
                    "name": feed.feed.get("itunes_owner", {}).get("name"),
                    "email": feed.feed.get("itunes_owner", {}).get("email"),
                } if feed.feed.get("itunes_owner") else None,
                "itunesType": feed.feed.get("itunes_type"),
                "categories": [],
                "socialMedia": [],
                "episodes": [],
            }

            if hasattr(feed.feed, "tags"):
                for tag in feed.feed.tags:
                    term = tag.get("term")
                    scheme = tag.get("scheme")
                    if scheme and "itunes" in scheme.lower() and term:
                        parsed_data["categories"].append({"main": term, "subcategories": []})
                    elif term:
                        parsed_data["categories"].append({"main": term, "subcategories": []})

            if not parsed_data["imageUrl"] and hasattr(feed.feed, 'itunes_image') and feed.feed.itunes_image:
                parsed_data["imageUrl"] = feed.feed.itunes_image.get('href')

            parsed_episodes = []
            for entry in feed.entries:
                episode_pub_date_obj = self._ensure_utc(entry.get("published_parsed") or entry.get("updated_parsed"))

                episode_data = {
                    "title": entry.get("title"),
                    "description": self._sanitize_html(entry.get("description") or entry.get("summary")),
                    "summary": self._sanitize_html(entry.get("summary") or entry.get("itunes_summary")),
                    "subtitle": self._sanitize_html(entry.get("subtitle") or entry.get("itunes_subtitle")),
                    "pubDate": episode_pub_date_obj.isoformat() if episode_pub_date_obj else None,
                    "link": entry.get("link"),
                    "guid": entry.get("id") or entry.get("guid"),
                    "author": entry.get("author_detail", {}).get("name") if entry.get("author_detail") else entry.get("author"),
                    "duration": self._parse_duration(entry.get("itunes_duration")),
                    "explicit": entry.get("itunes_explicit"),
                    "season": entry.get("itunes_season"),
                    "episode": entry.get("itunes_episode"),
                    "episodeType": entry.get("itunes_episodetype"),
                    "image": entry.get("image", {}).get("href") if entry.get("image") else (entry.get("itunes_image", {}).get("href") if entry.get("itunes_image") else None),
                    "audio": None,
                    "chapters": entry.get("psc_chapters", {}).get("chapters", []) if hasattr(entry, 'psc_chapters') else [],
                    "keywords": [tag.term for tag in entry.get("tags", [])],
                }

                if hasattr(entry, "enclosures"):
                    for enc in entry.enclosures:
                        if enc.get("type", "").startswith("audio/"):
                            episode_data["audio"] = {
                                "url": enc.get("href"),
                                "type": enc.get("type"),
                                "length": int(enc.get("length", 0)),
                            }
                            break

                parsed_episodes.append(episode_data)

            parsed_data["episodes"] = parsed_episodes
            logger.info(f"Successfully parsed {len(parsed_episodes)} episodes from feed: {feed_url}")
            return parsed_data, 200

        except Exception as e:
            logger.error(f"❌ Error parsing RSS content for {feed_url}: {e}", exc_info=True)
            return {"error": f"Failed to parse RSS content: {str(e)}"}, 500

    def fetch_rss_feed(self, rss_url):
        response = None
        try:
            logger.info(f"🌐 Fetching RSS feed from URL: {rss_url}")
            headers = {'User-Agent': 'PodManager/1.0'}
            logger.debug(f"Attempting requests.get for {rss_url} with headers: {headers} and timeout: 10s")
            response = requests.get(rss_url, timeout=10, headers=headers)
            logger.debug(f"Received response with status code: {response.status_code} for {rss_url}")

            if not response.ok:
                logger.error(f"Response not OK for {rss_url}. Status: {response.status_code}. Response text (first 500 chars): {response.text[:500] if response.text else 'No response text'}")
            response.raise_for_status()

            parsed_data, status_code = self.parse_rss_data(response.content, rss_url)
            return parsed_data, status_code

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed for RSS feed {rss_url}. Type: {type(e).__name__}, Error: {e}", exc_info=True)
            return {"error": f"Failed to fetch RSS feed: {type(e).__name__} - {str(e)}"}, 500
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching RSS feed {rss_url}. Type: {type(e).__name__}, Error: {e}", exc_info=True)
            return {"error": f"Failed to process RSS feed: {type(e).__name__} - {str(e)}"}, 500
