import logging
from xml.etree.ElementTree import Element, SubElement, tostring
from backend.services.upload_rss_to_google_cloud import upload_rss_to_google_cloud

logger = logging.getLogger(__name__)

def create_rss_feed(podcast, episodes):
    """
    Generate an RSS feed for the given podcast and episodes.
    """
    try:
        rss = Element("rss", version="2.0", attrib={"xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"})
        channel = SubElement(rss, "channel")

        # Add podcast details
        SubElement(channel, "title").text = podcast.get("podName", "Untitled Podcast")
        SubElement(channel, "description").text = podcast.get("description", "No description available")
        SubElement(channel, "link").text = podcast.get("podUrl", "#")
        SubElement(channel, "language").text = podcast.get("language", "en-us")
        SubElement(channel, "itunes:author").text = podcast.get("author", "Unknown Author")
        SubElement(channel, "itunes:explicit").text = "yes" if podcast.get("explicit", False) else "no"

        # Add podcast image
        image_url = podcast.get("imageUrl", "")
        if image_url:
            image = SubElement(channel, "itunes:image", href=image_url)

        # Add episodes
        for episode in episodes:
            item = SubElement(channel, "item")
            SubElement(item, "title").text = episode.get("title", "Untitled Episode")
            SubElement(item, "description").text = episode.get("description", "No description available")
            SubElement(item, "pubDate").text = episode.get("publishDate", "Unknown")
            SubElement(item, "guid").text = episode.get("guid", "")
            SubElement(item, "enclosure", url=episode.get("audioUrl", ""), type="audio/mpeg")
            SubElement(item, "itunes:duration").text = str(episode.get("duration", 0))
            SubElement(item, "itunes:explicit").text = "yes" if episode.get("explicit", False) else "no"

        # Convert to string
        rss_feed = tostring(rss, encoding="utf-8").decode("utf-8")
        logger.info("RSS feed created successfully.")
        return rss_feed
    except Exception as e:
        logger.error(f"Error creating RSS feed: {e}")
        raise
