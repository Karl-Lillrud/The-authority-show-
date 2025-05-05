import urllib.request
import urllib.error  # Import error module
import feedparser
import re
import logging

logger = logging.getLogger(__name__)  # Configure logger


class RSSService:
    @staticmethod
    def fetch_rss_feed(rss_url):
        """
        Fetches and parses an RSS feed, extracting podcast metadata and episodes.
        Returns a tuple: (data_dict, status_code)
        """
        try:
            logger.info(f"🌐 Fetching RSS feed from URL: {rss_url}")
            req = urllib.request.Request(
                rss_url,
                headers={"User-Agent": "Mozilla/5.0 (PodManager.ai RSS Parser)"},
            )
            # Add a timeout to the request
            with urllib.request.urlopen(req, timeout=20) as response:  # Added timeout=20 seconds
                rss_content = response.read()
                # Check status code from the response object itself if needed, though urlopen raises on error
                status_code = response.getcode()
                if status_code != 200:
                    logger.warning(f"Received non-200 status code {status_code} for {rss_url}")
            logger.info(f"✅ Successfully fetched RSS content for {rss_url}")

            # Parse the RSS feed using feedparser
            feed = feedparser.parse(rss_content)
            # Check for feedparser errors (bozo flag)
            if feed.bozo:
                bozo_exception = feed.get("bozo_exception", "Unknown parsing error")
                logger.warning(f"⚠️ Feedparser encountered issues parsing {rss_url}: {bozo_exception}")

            logger.info(f"✅ Successfully parsed RSS feed for {rss_url}")

            # --- Extract basic podcast info ---
            title = feed.feed.get("title", "")
            description = feed.feed.get("description", "")
            link = feed.feed.get("link", "")
            image_url = feed.feed.get("image", {}).get("href", "")
            language = feed.feed.get("language", "")
            author = feed.feed.get("author", "")
            copyright_info = feed.feed.get("copyright", "")
            generator = feed.feed.get("generator", "")
            last_build_date = feed.feed.get("lastBuildDate", "")
            itunes_type = feed.feed.get("itunes_type", "")
            itunes_owner_dict = feed.feed.get("itunes_owner", {})
            itunes_owner = {
                "name": itunes_owner_dict.get("itunes_name", "")
                or feed.feed.get("itunes_owner_name", "")
                or "",
                "email": itunes_owner_dict.get("itunes_email", "")
                or feed.feed.get("itunes_owner_email", "")
                or feed.feed.get("owner", {}).get("email", "")
                or feed.feed.get("owner_email", ""),
            }
            if not itunes_owner.get("email"):
                try:
                    rss_text = rss_content.decode("utf-8", errors="ignore")
                    match = re.search(
                        r"<itunes:email>(.*?)<\/itunes:email>", rss_text, re.IGNORECASE
                    )
                    if match:
                        itunes_owner["email"] = match.group(1).strip()
                except Exception as decode_err:
                    logger.warning(f"Could not decode or search content for email fallback in {rss_url}: {decode_err}")

            # --- Handle categories ---
            categories = []
            for cat in feed.feed.get("itunes_categories", []):
                main_cat = cat.get("text", "")
                sub_cats = [sub.get("text", "") for sub in cat.get("subcategories", [])]
                categories.append({"main": main_cat, "subcategories": sub_cats})
            if not categories and feed.feed.get("itunes_category"):
                categories.append(
                    {
                        "main": feed.feed.get("itunes_category", {}).get("text", ""),
                        "subcategories": [],
                    }
                )

            # --- Extract episodes ---
            episodes = []
            for entry in feed.entries:
                duration = entry.get("itunes_duration", "")
                duration_seconds = None
                if duration:
                    try:
                        if ":" in duration:
                            time_parts = duration.split(":")
                            if len(time_parts) == 3:  # HH:MM:SS
                                duration_seconds = (
                                    int(time_parts[0]) * 3600
                                    + int(time_parts[1]) * 60
                                    + int(time_parts[2])
                                )
                            elif len(time_parts) == 2:  # MM:SS
                                duration_seconds = int(time_parts[0]) * 60 + int(time_parts[1])
                        else:  # Assume seconds if no colon
                            duration_seconds = int(duration)
                    except (ValueError, IndexError):
                        logger.debug(f"Could not parse duration '{duration}' for an episode in {rss_url}")
                        duration_seconds = None

                episode_image = (
                    entry.get("itunes_image", {}).get("href", "")
                    or entry.get("image", {}).get("href", "")
                    or entry.get("media_thumbnail", [{}])[0].get("url", "")
                )

                episode = {
                    "title": entry.get("title", ""),
                    "description": entry.get("description", ""),
                    "pubDate": entry.get("published", ""),
                    "audio": {
                        "url": entry.get("enclosures", [{}])[0].get("href", ""),
                        "type": entry.get("enclosures", [{}])[0].get("type", ""),
                        "length": entry.get("enclosures", [{}])[0].get("length", ""),
                    },
                    "guid": entry.get("guid", ""),
                    "season": entry.get("itunes_season", None),
                    "episode": entry.get("itunes_episode", None),
                    "episodeType": entry.get("itunes_episodetype", None),
                    "explicit": entry.get("itunes_explicit", None),
                    "image": episode_image,
                    "keywords": entry.get("itunes_keywords", None),
                    "chapters": entry.get("chapters", None),
                    "link": entry.get("link", ""),
                    "subtitle": entry.get("itunes_subtitle", ""),
                    "summary": entry.get("itunes_summary", ""),
                    "author": entry.get("author", ""),
                    "isHidden": entry.get("itunes_isHidden", None),
                    "duration": duration_seconds,
                    "isImported": True,
                }
                episodes.append(episode)

            # --- Process imageUrl and logoUrl ---
            logo_url = image_url if image_url else None

            logger.info(f"✅ Successfully processed RSS feed data for {rss_url}")
            return {
                "title": title,
                "description": description,
                "link": link,
                "imageUrl": image_url,
                "logoUrl": logo_url,
                "language": language,
                "author": author,
                "copyright_info": copyright_info,
                "generator": generator,
                "lastBuildDate": last_build_date,
                "itunesType": itunes_type,
                "itunesOwner": itunes_owner,
                "email": itunes_owner.get("email", ""),
                "categories": categories,
                "episodes": episodes,
            }, 200

        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.warning(f"Feed not found (404) at URL: {rss_url}")
                return {"error": f"Feed not found (404): {rss_url}"}, 404
            elif e.code == 403:
                logger.warning(f"Access forbidden (403) for URL: {rss_url}")
                return {"error": f"Access forbidden (403): {rss_url}"}, 403
            elif e.code == 410:
                logger.warning(f"Feed gone (410) at URL: {rss_url}")
                return {"error": f"Feed gone (410): {rss_url}"}, 410
            else:
                logger.error(f"❌ HTTP Error {e.code} fetching RSS feed: {rss_url} - {e.reason}", exc_info=False)
                return {"error": f"HTTP Error {e.code}: {e.reason}"}, e.code

        except urllib.error.URLError as e:
            logger.error(f"❌ URL Error fetching RSS feed: {rss_url} - {e.reason}", exc_info=False)
            return {"error": f"URL Error: {e.reason}"}, 503

        except Exception as e:
            logger.error(f"❌ Unexpected error processing RSS feed {rss_url}: {e}", exc_info=True)
            return {"error": f"Unexpected error processing feed: {str(e)}"}, 500
