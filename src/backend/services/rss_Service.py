import requests
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

# Define ITMS_NS for iTunes specific tags
ITMS_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"

class RSSService:
    def fetch_rss_feed(self, rss_url):
        """Fetch and parse the RSS feed."""
        response = None # Initialize response to None
        try:
            logger.info(f"🌐 Fetching RSS feed from URL: {rss_url}")
            headers = {'User-Agent': 'PodManager/1.0'}
            logger.debug(f"Attempting requests.get for {rss_url} with headers: {headers} and timeout: 10s")
            response = requests.get(rss_url, timeout=10, headers=headers)
            logger.debug(f"Received response with status code: {response.status_code} for {rss_url}")

            if not response.ok:
                logger.error(f"Response not OK for {rss_url}. Status: {response.status_code}. Response text (first 500 chars): {response.text[:500] if response.text else 'No response text'}")
            response.raise_for_status()

            ET.register_namespace("itunes", ITMS_NS)
            root = ET.fromstring(response.content)
            
            channel = root.find("channel")
            if channel is None:
                logger.error(f"No <channel> element found in RSS feed: {rss_url}")
                return {"error": "Invalid RSS feed structure: missing channel"}, 400

            title_element = channel.find("title")
            title = title_element.text if title_element is not None else "Untitled Podcast"

            # Try to find image URL in various common places
            image_url = None
            # Standard RSS image
            image_tag = channel.find("image/url")
            if image_tag is not None and image_tag.text:
                image_url = image_tag.text
            
            # iTunes specific image
            if not image_url:
                itunes_image_tag = channel.find("{%s}image" % ITMS_NS)
                if itunes_image_tag is not None and itunes_image_tag.get("href"):
                    image_url = itunes_image_tag.get("href")
            
            # Fallback: look for image in feed-level content:encoded or description (less common for main image)
            if not image_url:
                logger.warning(f"Could not find standard or iTunes image for {rss_url}. Check feed structure.")

            episodes = []
            for item in channel.findall("item"):
                episode_title_element = item.find("title")
                episode_title = episode_title_element.text if episode_title_element is not None else "Untitled Episode"
                
                description_element = item.find("description")
                description = description_element.text if description_element is not None else ""
                
                pub_date_element = item.find("pubDate")
                pub_date = pub_date_element.text if pub_date_element is not None else None
                
                duration_element = item.find("{%s}duration" % ITMS_NS) # iTunes duration
                duration = duration_element.text if duration_element is not None else None
                
                enclosure_element = item.find("enclosure")
                audio_url = enclosure_element.attrib.get("url") if enclosure_element is not None and enclosure_element.attrib.get("url") else None
                
                episodes.append({
                    "title": episode_title,
                    "description": description,
                    "publishDate": pub_date,
                    "duration": duration,
                    "audioUrl": audio_url,
                })

            logger.info(f"✅ Successfully fetched and parsed RSS feed: {rss_url}")
            return {"title": title, "imageUrl": image_url, "episodes": episodes}, 200
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed for RSS feed {rss_url}. Type: {type(e).__name__}, Error: {e}", exc_info=True)
            return {"error": f"Failed to fetch RSS feed: {type(e).__name__} - {str(e)}"}, 500
        except ET.ParseError as e:
            logger.error(f"XML parsing failed for RSS feed {rss_url}: {e}", exc_info=True)
            if response is not None:
                try:
                    problematic_content = response.content.decode(errors='ignore')[:500]
                    logger.error(f"Content that failed XML parsing (first 500 chars): {problematic_content}")
                except Exception as log_err:
                    logger.error(f"Error logging problematic content for XML ParseError: {log_err}")
            else:
                logger.error("Could not log content for XML ParseError as 'response' object is not available (request might have failed earlier).")
            return {"error": f"Invalid XML in RSS feed: {str(e)}"}, 400
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching RSS feed {rss_url}. Type: {type(e).__name__}, Error: {e}", exc_info=True)
            return {"error": f"Failed to process RSS feed: {type(e).__name__} - {str(e)}"}, 500
