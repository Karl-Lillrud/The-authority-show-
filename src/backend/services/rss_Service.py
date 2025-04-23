import urllib.request
import feedparser
import re
import logging

logger = logging.getLogger(__name__)  # Configure logger


class RSSService:
    @staticmethod
    def fetch_rss_feed(rss_url):
        """
        Fetches and parses an RSS feed, extracting podcast metadata and episodes.
        """
        try:
            logger.info(f"🌐 Fetching RSS feed from URL: {rss_url}")  # Log start
            # Fetch the RSS feed
            req = urllib.request.Request(
                rss_url,
                headers={"User-Agent": "Mozilla/5.0 (PodManager.ai RSS Parser)"},
            )
            with urllib.request.urlopen(req) as response:
                rss_content = response.read()
            logger.info("✅ Successfully fetched RSS content")  # Log success

            # Parse the RSS feed using feedparser
            feed = feedparser.parse(rss_content)
            logger.info("✅ Successfully parsed RSS feed")  # Log parsing success

            # Extract basic podcast info
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
                rss_text = rss_content.decode("utf-8", errors="ignore")
                match = re.search(
                    r"<itunes:email>(.*?)<\/itunes:email>", rss_text, re.IGNORECASE
                )
                if match:
                    itunes_owner["email"] = match.group(1).strip()

            # Handle categories and subcategories
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
            if not categories:
                rss_text = rss_content.decode("utf-8", errors="ignore")
                cat_matches = re.findall(
                    r'<itunes:category text="([^"]+)"', rss_text, re.IGNORECASE
                )
                if cat_matches:
                    categories = [{"main": m, "subcategories": []} for m in cat_matches]

            # Extract episodes
            episodes = []
            for entry in feed.entries:
                duration = entry.get("itunes_duration", "")
                duration_seconds = None
                if duration and ":" in duration:
                    time_parts = duration.split(":")
                    if len(time_parts) == 3:  # HH:MM:SS
                        duration_seconds = (
                            int(time_parts[0]) * 3600
                            + int(time_parts[1]) * 60
                            + int(time_parts[2])
                        )
                    elif len(time_parts) == 2:  # MM:SS
                        duration_seconds = int(time_parts[0]) * 60 + int(time_parts[1])

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

            # Process imageUrl and logoUrl
            logo_url = image_url if image_url else None

            logger.info(
                "✅ Successfully processed RSS feed data"
            )  # Log processing success
            return {
                "title": title,
                "description": description,
                "link": link,
                "imageUrl": image_url,
                "logoUrl": logo_url,  # Add processed logoUrl
                "language": language,
                "author": author,
                "copyright_info": copyright_info,
                "generator": generator,
                "lastBuildDate": last_build_date,
                "itunesType": itunes_type,
                "itunesOwner": itunes_owner,
                "email": itunes_owner.get("email", ""),
                "categories": categories,
                "episodes": episodes  
            }, 200

        except Exception as e:
            logger.error(
                "❌ ERROR fetching RSS feed: %s", e, exc_info=True
            )  # Log error
            return {"error": f"Error fetching RSS feed: {str(e)}"}, 500
