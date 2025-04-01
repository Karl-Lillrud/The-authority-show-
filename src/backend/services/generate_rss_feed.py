import logging
from xml.etree.ElementTree import Element, SubElement, tostring

logger = logging.getLogger(__name__)

def create_rss_feed(podcast, episodes):
    """
    Generate an RSS feed for the given podcast and episodes.
    """
    try:
        rss = Element("rss", version="2.0")
        channel = SubElement(rss, "channel")

        # Add podcast details
        SubElement(channel, "title").text = podcast.get("podName", "Untitled Podcast")
        SubElement(channel, "description").text = podcast.get("description", "No description available")
        SubElement(channel, "link").text = podcast.get("podUrl", "#")

        # Add episodes
        for episode in episodes:
            item = SubElement(channel, "item")
            SubElement(item, "title").text = episode.get("title", "Untitled Episode")
            SubElement(item, "description").text = episode.get("description", "No description available")
            SubElement(item, "pubDate").text = episode.get("publishDate", "Unknown")
            SubElement(item, "guid").text = episode.get("guid", "")
            SubElement(item, "enclosure", url=episode.get("audioUrl", ""), type="audio/mpeg")

        rss_feed = tostring(rss, encoding="utf-8").decode("utf-8")
        logger.info("RSS feed created successfully.")
        return rss_feed
    except Exception as e:
        logger.error(f"Error creating RSS feed: {e}")
        raise
