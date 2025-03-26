import xml.etree.ElementTree as ET

def create_rss_feed(podcast, episodes):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    title = ET.SubElement(channel, "title")
    title.text = podcast['title']

    description = ET.SubElement(channel, "description")
    description.text = podcast['description']

    link = ET.SubElement(channel, "link")
    link.text = podcast['link']

    for episode in episodes:
        item = ET.SubElement(channel, "item")
        
        episode_title = ET.SubElement(item, "title")
        episode_title.text = episode['title']
        
        episode_description = ET.SubElement(item, "description")
        episode_description.text = episode['description']
        
        episode_publish_date = ET.SubElement(item, "pubDate")
        episode_publish_date.text = episode['publish_date']
        
        audio_url = ET.SubElement(item, "enclosure", url=episode['audio_url'], type="audio/mpeg")
        
        episode_guid = ET.SubElement(item, "guid")
        episode_guid.text = episode['guid']
        
    # Generate the XML string of the RSS feed
    rss_feed = ET.tostring(rss, encoding="utf-8", method="xml").decode()
    
    # Save to file (optional)
    with open(f"{podcast['title']}_feed.xml", "w") as file:
        file.write(rss_feed)

    return rss_feed

