import logging
from xml.etree.ElementTree import Element, SubElement, tostring
from email.utils import formatdate

logger = logging.getLogger(__name__)

def create_rss_feed(podcast, episodes):
    """
    Generate an RSS feed for the given podcast and episodes.
    """
    try:
        # Initialize the RSS structure
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
            SubElement(channel, "itunes:image", href=image_url)

        # Add lastBuildDate
        SubElement(channel, "lastBuildDate").text = formatdate(localtime=True)

        # Add episodes
        for episode in episodes:
            item = SubElement(channel, "item")
            SubElement(item, "title").text = episode.get("title", "Untitled Episode")
            SubElement(item, "description").text = episode.get("description", "No description available")

            # Handle the publishDate
            publish_date = episode.get("publishDate")
            if not publish_date:
                publish_date = formatdate(localtime=True)
            SubElement(item, "pubDate").text = publish_date

            # Add the episode GUID
            SubElement(item, "guid").text = episode.get("guid", "")

            # Add the enclosure (audio URL)
            audio_url = episode.get("audioUrl", "")
            if audio_url:
                SubElement(item, "enclosure", url=audio_url, type="audio/mpeg")

            # Add duration
            SubElement(item, "itunes:duration").text = str(episode.get("duration", 0))

            # Add explicit flag for the episode
            SubElement(item, "itunes:explicit").text = "yes" if episode.get("explicit", False) else "no"

        # Convert to string and return
        rss_feed = tostring(rss, encoding="utf-8").decode("utf-8")
        logger.info("RSS feed created successfully.")
        return rss_feed

    except Exception as e:
        logger.error(f"Error creating RSS feed: {e}")
        raise
