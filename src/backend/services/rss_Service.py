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
            ET.register_namespace("content", "http://purl.org/rss/1.0/modules/content/") # For content:encoded
            ET.register_namespace("podcast", "https://podcastindex.org/namespace/1.0") # For podcast namespace tags

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
                
                # Description: prefer content:encoded, then itunes:summary, then description
                description = ""
                content_encoded_element = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
                if content_encoded_element is not None and content_encoded_element.text:
                    description = content_encoded_element.text
                else:
                    itunes_summary_element = item.find("{%s}summary" % ITMS_NS)
                    if itunes_summary_element is not None and itunes_summary_element.text:
                        description = itunes_summary_element.text
                    else:
                        description_element = item.find("description")
                        if description_element is not None and description_element.text:
                            description = description_element.text
                
                pub_date_element = item.find("pubDate")
                pub_date = pub_date_element.text if pub_date_element is not None else None
                
                duration_element = item.find("{%s}duration" % ITMS_NS) # iTunes duration
                duration_str = duration_element.text if duration_element is not None else None
                # Convert duration (HH:MM:SS or seconds) to seconds if possible
                duration_seconds = None
                if duration_str:
                    if ':' in duration_str:
                        parts = list(map(int, duration_str.split(':')))
                        if len(parts) == 3: # HH:MM:SS
                            duration_seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
                        elif len(parts) == 2: # MM:SS
                            duration_seconds = parts[0] * 60 + parts[1]
                        else: # Potentially just seconds as string
                            try: duration_seconds = int(duration_str)
                            except ValueError: pass
                    else:
                        try: duration_seconds = int(duration_str)
                        except ValueError: pass
                
                enclosure_element = item.find("enclosure")
                audio_url = None
                file_size = None
                file_type = None
                if enclosure_element is not None:
                    audio_url = enclosure_element.get("url")
                    file_size = enclosure_element.get("length")
                    file_type = enclosure_element.get("type")
                    try: # Ensure fileSize is an int if present
                        if file_size is not None: file_size = int(file_size)
                    except ValueError:
                        logger.warning(f"Could not convert episode enclosure length '{file_size}' to int for '{episode_title}'.")
                        file_size = None

                guid_element = item.find("guid")
                guid = guid_element.text if guid_element is not None else None

                link_element = item.find("link")
                link = link_element.text if link_element is not None else None

                itunes_image_element = item.find("{%s}image" % ITMS_NS)
                episode_image_url = itunes_image_element.get("href") if itunes_image_element is not None else None
                
                itunes_season_element = item.find("{%s}season" % ITMS_NS)
                season = itunes_season_element.text if itunes_season_element is not None else None
                
                itunes_episode_element = item.find("{%s}episode" % ITMS_NS)
                episode_num_str = itunes_episode_element.text if itunes_episode_element is not None else None
                
                itunes_episode_type_element = item.find("{%s}episodeType" % ITMS_NS)
                episode_type = itunes_episode_type_element.text if itunes_episode_type_element is not None else "full" # Default to full

                itunes_explicit_element = item.find("{%s}explicit" % ITMS_NS)
                explicit_str = itunes_explicit_element.text.lower() if itunes_explicit_element is not None and itunes_explicit_element.text else "no"
                explicit = True if explicit_str in ["yes", "true"] else False

                itunes_author_element = item.find("{%s}author" % ITMS_NS)
                author = itunes_author_element.text if itunes_author_element is not None else None
                
                itunes_subtitle_element = item.find("{%s}subtitle" % ITMS_NS)
                subtitle = itunes_subtitle_element.text if itunes_subtitle_element is not None else None

                # Keywords are often comma-separated
                itunes_keywords_element = item.find("{%s}keywords" % ITMS_NS)
                keywords = [k.strip() for k in itunes_keywords_element.text.split(',')] if itunes_keywords_element is not None and itunes_keywords_element.text else []


                episodes.append({
                    "title": episode_title,
                    "description": description, # This is now more comprehensive
                    "summary": item.findtext("{%s}summary" % ITMS_NS, default=description), # itunes:summary or fallback
                    "subtitle": subtitle,
                    "publishDate": pub_date, # Keep as string, schema handles conversion
                    "duration": duration_seconds, # Send as integer seconds
                    "audioUrl": audio_url,
                    "fileSize": file_size, # Send as integer
                    "fileType": file_type,
                    "guid": guid,
                    "link": link,
                    "imageUrl": episode_image_url or image_url, # Episode image or fallback to channel image
                    "season": season,
                    "episode": episode_num_str, # Keep as string, schema handles conversion
                    "episodeType": episode_type,
                    "explicit": explicit, # Send as boolean
                    "author": author,
                    "keywords": keywords,
                    # "chapters": None, # Placeholder for future implementation
                    # "isHidden": False, # Default, not typically in RSS
                })

            logger.info(f"✅ Successfully fetched and parsed RSS feed: {rss_url}, found {len(episodes)} episodes.")
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
