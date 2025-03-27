from datetime import datetime
import xml.etree.ElementTree as ET

def create_rss_feed(podcast, episodes):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    
    title = ET.SubElement(channel, "title")
    title.text = podcast.get('title', 'Untitled Podcast')  # Handle None value

    description = ET.SubElement(channel, "description")
    description.text = podcast.get('description', 'No description available')  # Handle None value

    link = ET.SubElement(channel, "link")
    link.text = podcast.get('link', '#')  # Handle None value

    image = ET.SubElement(channel, "image")
    image_url = ET.SubElement(image, "url")
    image_url.text = podcast.get('imageUrl', 'default-image.png')  # Ensure image URL is included

    author = ET.SubElement(channel, "author")
    author.text = podcast.get('author', 'Unknown Author')  # Ensure author is included

    explicit = ET.SubElement(channel, "explicit")
    explicit.text = "yes" if podcast.get('explicit', False) else "no"  # Explicit content flag

    category = ET.SubElement(channel, "category")
    category.text = podcast.get('category', 'Uncategorized')  # Ensure category is included

    for episode in episodes:
        item = ET.SubElement(channel, "item")
        
        episode_title = ET.SubElement(item, "title")
        episode_title.text = episode.get('title', 'Untitled Episode')  # Handle None value
        
        episode_description = ET.SubElement(item, "description")
        episode_description.text = episode.get('description', 'No description available')  # Handle None value
        
        # Convert datetime to string before adding it to XML
        episode_publish_date = ET.SubElement(item, "pubDate")
        publish_date = episode.get('publish_date', None)
        if isinstance(publish_date, datetime):
            episode_publish_date.text = publish_date.isoformat()  # Format datetime
        else:
            episode_publish_date.text = str(publish_date) if publish_date else 'Unknown'  # Handle None value
        
        audio_url = episode.get('audio_url', '#')  # Handle None value
        if not audio_url:  # Ensure audio_url is not None or empty
            audio_url = '#'
        audio_enclosure = ET.SubElement(item, "enclosure", url=audio_url, type="audio/mpeg")
        
        episode_guid = ET.SubElement(item, "guid")
        episode_guid.text = episode.get('guid', 'Unknown')  # Handle None value
        
    # Generate the XML string of the RSS feed
    rss_feed = ET.tostring(rss, encoding="utf-8", method="xml").decode()
    
    # Save to file (optional)
    with open(f"{podcast['title']}_feed.xml", "w") as file:
        file.write(rss_feed)

    return rss_feed
