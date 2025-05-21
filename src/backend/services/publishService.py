import os
import datetime
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from pymongo import MongoClient
from bson.objectid import ObjectId
from xml.etree.ElementTree import Element, SubElement, tostring
from io import BytesIO
import threading
import requests
import time
from flask import current_app

AZURE_CONN_STR = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
CONTAINER_NAME = os.getenv('AZURE_BLOB_CONTAINER', 'podcast-audio')

blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

MONGO_URI = os.getenv('MONGO_URI')
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['podcast_db']
episodes_col = db['episodes']
podcasts_col = db['podcasts']
downloads_col = db['downloads']

# === SAS URL Generation ===
def create_sas_upload_url(filename, content_type):
    blob_name = f"uploads/{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=CONTAINER_NAME,
        blob_name=blob_name,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(write=True),
        expiry=datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
        content_type=content_type,
    )
    upload_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{blob_name}?{sas_token}"
    blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{blob_name}"
    return upload_url, blob_url


# === Save Episode Metadata ===
def save_episode_to_db(data, publish_date):
    episode_doc = {
        "title": data['title'],
        "description": data['description'],
        "episodeNumber": data['episodeNumber'],
        "seasonNumber": data['seasonNumber'],
        "explicit": data['explicit'],
        "audioUrl": data['audioUrl'],
        "publishDate": publish_date,
        "status": "uploaded",
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow(),
    }
    result = episodes_col.insert_one(episode_doc)
    return result.inserted_id


# === Trigger Encoding (simulate or call Azure Function) ===
def trigger_encoding_job(episode_id):
    # Replace with Azure Function HTTP call or Queue trigger in prod
    def encoding_sim():
        import time
        time.sleep(10)  # simulate encoding time
        episodes_col.update_one(
            {"_id": ObjectId(episode_id)},
            {"$set": {"status": "encoded", "updatedAt": datetime.datetime.utcnow()}}
        )
    threading.Thread(target=encoding_sim).start()


# === RSS Feed Generation ===
def generate_rss_feed(podcast_id):
    # For simplicity: get all episodes for podcast_id ordered by publishDate
    # Here podcast_id is a string, you may map podcasts separately in your model
    episodes = list(episodes_col.find({"status": "encoded", "publishDate": {"$lte": datetime.datetime.utcnow()}}).sort("publishDate", 1))

    rss = Element('rss', version='2.0', attrib={
        'xmlns:itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        'xmlns:media': 'http://search.yahoo.com/mrss/'
    })
    channel = SubElement(rss, 'channel')
    SubElement(channel, 'title').text = "Your Podcast Title"
    SubElement(channel, 'link').text = "https://yourdomain.com/podcast/" + podcast_id
    SubElement(channel, 'description').text = "Podcast description here"
    SubElement(channel, 'language').text = "en-us"
    SubElement(channel, 'itunes:explicit').text = "yes" if any(e['explicit'] for e in episodes) else "no"

    for ep in episodes:
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = ep['title']
        SubElement(item, 'description').text = ep['description']
        SubElement(item, 'pubDate').text = ep['publishDate'].strftime('%a, %d %b %Y %H:%M:%S GMT')
        SubElement(item, 'guid').text = str(ep['_id'])
        enclosure = SubElement(item, 'enclosure')
        enclosure.set('url', ep['audioUrl'])
        enclosure.set('type', 'audio/mpeg')
        # Add iTunes tags as needed
        SubElement(item, 'itunes:episode').text = str(ep.get('episodeNumber', 1))
        SubElement(item, 'itunes:season').text = str(ep.get('seasonNumber', 1))
        SubElement(item, 'itunes:explicit').text = "yes" if ep.get('explicit', False) else "no"

    xml_str = tostring(rss, encoding='utf-8')
    return xml_str


# === Download Analytics ===
def record_download(episode_id):
    downloads_col.insert_one({
        "episodeId": ObjectId(episode_id),
        "timestamp": datetime.datetime.utcnow(),
        # Optionally add IP, user-agent etc
    })


# === Audio Proxy Stream ===
def get_episode_audio_stream(episode_id):
    ep = episodes_col.find_one({"_id": ObjectId(episode_id)})
    if not ep:
        raise Exception("Episode not found")

    url = ep['audioUrl']
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        raise Exception("Failed to fetch audio")

    # Return raw stream as file-like object
    return BytesIO(r.content)


# === Podcast Directory Notifications (stubs) ===
def notify_spotify(episode_id):
    # Use Spotify Podcast API with OAuth2 token
    # For demo, just log
    print(f"Notify Spotify about episode {episode_id}")


def notify_google_podcasts(episode_id):
    # Google Podcasts uses RSS feed URL submit - manual for now or via Search Console API
    print(f"Notify Google Podcasts about episode {episode_id}")


# === Publish Service ===
class PublishService:
    def __init__(self):
        # self.episode_repo = EpisodeRepository() # Example
        # self.podcast_repo = PodcastRepository() # Example
        pass

    def publish_episode(self, episode_id, platforms, notes):
        """
        Handles the logic for publishing an episode to the specified platforms.
        This is a placeholder and should be implemented with actual publishing integrations.
        """
        current_app.logger.info(f"PublishService: Attempting to publish episode {episode_id} to {platforms}. Notes: '{notes}'")

        # --- Placeholder Logic ---
        # 1. Fetch episode details (audio file, metadata, etc.)
        # episode = self.episode_repo.get_by_id(episode_id)
        # if not episode:
        #     return {"success": False, "error": "Episode not found"}
        #
        # podcast = self.podcast_repo.get_by_id(episode.podcast_id) # Assuming episode has podcast_id
        # if not podcast:
        #     return {"success": False, "error": "Associated podcast not found"}

        # 2. For each platform in 'platforms':
        #    - Check if integration is configured (e.g., API keys for Spotify, Apple via RSS update)
        #    - Perform platform-specific publishing actions
        #    - Log success/failure for each platform

        log_messages = []

        for platform in platforms:
            log_messages.append(f"Simulating publishing to {platform}...")
            time.sleep(1) # Simulate work
            # Example:
            # if platform == "spotify":
            #   result = self._publish_to_spotify(episode, podcast)
            #   log_messages.append(f"Spotify: {result['message']}")
            # elif platform == "apple":
            #   # Apple Podcasts usually updates via RSS feed changes.
            #   # This might involve ensuring the episode is in the RSS feed and the feed is valid.
            #   log_messages.append("Apple Podcasts: RSS feed update simulated.")
            # else:
            #   log_messages.append(f"Platform '{platform}' not yet implemented.")
            log_messages.append(f"Successfully simulated publishing to {platform}.")
        
        # --- End Placeholder Logic ---

        # In a real scenario, you'd collect results from actual API calls.
        # For now, we assume success.
        
        # Update episode status to 'Published' or similar
        # self.episode_repo.update_episode_status(episode_id, "Published", platforms_published_to=platforms)
        
        current_app.logger.info(f"PublishService: Successfully processed publish request for episode {episode_id}.")
        return {
            "success": True,
            "message": f"Episode {episode_id} processed for publishing to {', '.join(platforms)}.",
            "details": log_messages
        }

    # Example placeholder for a specific platform
    # def _publish_to_spotify(self, episode_data, podcast_data):
    #     # Connect to Spotify API, upload audio, metadata, etc.
    #     return {"success": True, "message": "Published to Spotify (simulated)"}
