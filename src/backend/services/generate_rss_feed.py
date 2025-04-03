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

        # Add podcast image (cover art)
        image_url = podcast.get("imageUrl", "https://storage.googleapis.com/podmanager/images/default_image.png")
        SubElement(channel, "itunes:image", href=image_url)
        logger.info(f"Podcast image URL added to RSS feed: {image_url}")

        # Add iTunes categories (at least one is required)
        categories = podcast.get("categories", ["Uncategorized"])
        for category in categories:
            SubElement(channel, "itunes:category", text=category)

        # Add episodes
        for episode in episodes:
            item = SubElement(channel, "item")

            # Populate <item> with episode-specific data
            SubElement(item, "title").text = episode.get("title", "Untitled Episode")
            SubElement(item, "description").text = episode.get("description", "No description available")

            # Set the pubDate in RFC-822 format, default to the current time if unavailable
            pub_date = episode.get("publishDate")
            if pub_date:
                pub_date = datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%S.%f%z")  # Convert from ISO format
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

            # Add duration (if available)
            duration = episode.get("duration", "0")
            SubElement(item, "itunes:duration").text = duration

            # Add explicit content flag for episodes
            explicit = episode.get("explicit", False)
            SubElement(item, "itunes:explicit").text = "true" if explicit else "false"

        # Convert to string and generate the final RSS XML
        rss_feed = tostring(rss, encoding="utf-8").decode("utf-8")
        logger.info("RSS feed created successfully.")
        return rss_feed
    except Exception as e:
        logger.error(f"Error creating RSS feed: {e}")
        raise