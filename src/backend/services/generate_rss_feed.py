import logging
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime
import mimetypes

logger = logging.getLogger(__name__)

def create_rss_feed(podcast, episodes):
    """
    Generate an RSS feed for the given podcast and episodes.
    """
    try:
        # Create the root <rss> element with the required namespaces
        rss = Element(
            "rss",
            version="2.0",
            attrib={
                "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
                "xmlns:media": "http://search.yahoo.com/mrss/",
                "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
            },
        )
        channel = SubElement(rss, "channel")

        # Add podcast details
        SubElement(channel, "title").text = podcast.get("podName", "Untitled Podcast")
        SubElement(channel, "description").text = podcast.get("description", "No description available")
        SubElement(channel, "link").text = podcast.get("rssFeedUrl", "#")
        SubElement(channel, "language").text = podcast.get("language", "en-us")
        SubElement(channel, "itunes:author").text = podcast.get("author", "Unknown Author")
        SubElement(channel, "itunes:explicit").text = "true" if podcast.get("explicit", False) else "false"
        SubElement(channel, "itunes:type").text = podcast.get("type", "episodic")  # Default to episodic
        SubElement(channel, "copyright").text = podcast.get("copyright_info", "Copyright information not provided")
        SubElement(channel, "itunes:summary").text = podcast.get("summary", "No summary available")

        # Add podcast image (cover art)
        image_url = podcast.get("imageUrl", "https://storage.googleapis.com/podmanager/images/default_image.png")
        SubElement(channel, "itunes:image", href=image_url)
        logger.info(f"Podcast image URL added to RSS feed: {image_url}")

        # Add iTunes owner details
        itunes_owner_name = podcast.get("itunesOwnerName", "Unknown Owner")
        itunes_owner_email = podcast.get("itunesOwnerEmail", "owner@example.com")
        itunes_owner = SubElement(channel, "itunes:owner")
        SubElement(itunes_owner, "itunes:name").text = itunes_owner_name
        SubElement(itunes_owner, "itunes:email").text = itunes_owner_email

        # Add iTunes categories (up to 3 categories with subcategories)
        categories = podcast.get("categories", ["Uncategorized"])
        for category in categories[:3]:  # Limit to 3 categories
            if isinstance(category, str):
                # If category is a string, add it directly
                SubElement(channel, "itunes:category", text=category)
            elif isinstance(category, dict):
                # If category is a dictionary, handle subcategories
                main_category = SubElement(channel, "itunes:category", text=category.get("main", "Uncategorized"))
                for subcategory in category.get("subcategories", [])[:1]:  # Limit to 1 subcategory per category
                    SubElement(main_category, "itunes:category", text=subcategory)

        # Add episodes
        for episode in episodes:
            item = SubElement(channel, "item")

            # Populate <item> with episode-specific data
            SubElement(item, "title").text = episode.get("title", "Untitled Episode")
            SubElement(item, "description").text = episode.get("description", "No description available")
            SubElement(item, "itunes:summary").text = episode.get("summary", "No summary available")
            SubElement(item, "itunes:author").text = episode.get("author", "Unknown Author")
            SubElement(item, "content:encoded").text = episode.get("contentEncoded", "No content available")

            # Set the pubDate in RFC-822 format, default to the current time if unavailable
            pub_date = episode.get("publishDate")
            if isinstance(pub_date, str):
                pub_date = datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%S.%f%z")  # Convert from ISO format
            if isinstance(pub_date, datetime):
                pub_date_str = pub_date.strftime("%a, %d %b %Y %H:%M:%S GMT")  # Convert to RFC-822
            else:
                pub_date_str = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
            SubElement(item, "pubDate").text = pub_date_str

            # Add <guid> (Episode ID or URL) - Ensure it's unique
            guid = episode.get("guid", f"https://yourdomain.com/episode/{episode.get('id', 'unknown')}")
            SubElement(item, "guid").text = guid

            # Add enclosure for the audio file
            audio_url = episode.get("audioUrl", "")
            if audio_url:
                mime_type, _ = mimetypes.guess_type(audio_url)
                if mime_type and mime_type.startswith("audio/"):
                    SubElement(item, "enclosure", url=audio_url, type=mime_type, length=str(episode.get("fileSize", 0)))
                else:
                    logger.warning(f"Invalid audio file URL or type: {audio_url}")
            else:
                logger.warning("Audio URL is missing for an episode.")
                continue  # Skip this episode if no audio URL is provided

            # Add episode image (if available)
            episode_image = episode.get("imageUrl", image_url)  # Fallback to podcast image
            SubElement(item, "itunes:image", href=episode_image)
            logger.info(f"Episode image URL added to RSS feed: {episode_image}")

            # Add duration (if available) and ensure it's a string
            duration = episode.get("duration", "0")
            SubElement(item, "itunes:duration").text = str(duration)

            # Add explicit content flag for episodes
            explicit = episode.get("explicit", False)
            SubElement(item, "itunes:explicit").text = "true" if explicit else "false"

            # Add link to the episode's webpage
            link = episode.get("link", "#")
            SubElement(item, "link").text = link

        # Convert to string and generate the final RSS XML
        rss_feed = tostring(rss, encoding="utf-8").decode("utf-8")
        logger.info("RSS feed created successfully.")
        return rss_feed
    except Exception as e:
        logger.error(f"Error creating RSS feed: {e}")
        raise