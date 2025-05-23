import os
import datetime
from flask import current_app, url_for, request # Added request
from backend.repository.episode_repository import EpisodeRepository
from backend.repository.podcast_repository import PodcastRepository
from backend.services.rss_Service import RSSService
from backend.utils.blob_storage import upload_file_to_blob  # For any generic blob uploads
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions # Modified import
import time # Add this import
from backend.database.mongo_connection import mongo # Import mongo

class PublishService:
    def __init__(self):
        self.episode_repo = EpisodeRepository()
        self.podcast_repo = PodcastRepository()
        self.rss_service = RSSService()
        self.rss_feed_base_url = os.getenv("RSS_FEED_BASE_URL")
        # Initialize Azure configuration for PublishService
        self.azure_storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.azure_storage_container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
        self.base_url = os.getenv("LOCAL_BASE_URL") if os.getenv("ENVIRONMENT") == "local" else os.getenv("PROD_BASE_URL")


    def _find_podcast_details_by_identifier(self, identifier_to_find):
        podcasts_collection = mongo.db.Podcasts 
        accounts_collection = mongo.db.Accounts
    
        matched_podcasts = []
        # Iterate through all podcasts, compare their names directly with the identifier.
        for p_data in podcasts_collection.find({}, {"_id": 1, "podName": 1, "accountId": 1}):
            current_pod_name = p_data.get("podName")
            # Direct comparison for podName
            if current_pod_name == identifier_to_find:
                account = accounts_collection.find_one({"_id": p_data.get("accountId")}, {"ownerId": 1})
                if account and account.get("ownerId"):
                    matched_podcasts.append({
                        "podcast_id": str(p_data["_id"]),
                        "user_id": str(account["ownerId"]) 
                    })
                else:
                    current_app.logger.warning(f"Found podcast with name '{identifier_to_find}' (ID: {p_data['_id']}) but could not find its account or ownerId.")
        
        if not matched_podcasts:
            try:
                if len(identifier_to_find) == 36: 
                    potential_podcast_by_id = podcasts_collection.find_one({"_id": identifier_to_find}, {"_id": 1, "accountId": 1})
                    if potential_podcast_by_id:
                        account = accounts_collection.find_one({"_id": potential_podcast_by_id.get("accountId")}, {"ownerId": 1})
                        if account and account.get("ownerId"):
                            current_app.logger.info(f"Interpreting '{identifier_to_find}' as a direct podcast_id for RSS proxy.")
                            return str(potential_podcast_by_id["_id"]), str(account["ownerId"])
            except Exception as e:
                current_app.logger.info(f"Could not interpret '{identifier_to_find}' as podcast_id during fallback: {e}")
            return None, None 
    
        if len(matched_podcasts) > 1:
            current_app.logger.warning(
                f"Multiple podcasts found for identifier (podName) '{identifier_to_find}'. Using the first one: {matched_podcasts[0]['podcast_id']}"
            )
        
        if not matched_podcasts: # Ensure we return None, None if still no matches after all checks
            return None, None

        return matched_podcasts[0]["podcast_id"], matched_podcasts[0]["user_id"]

    def publish_episode(self, episode_id, user_id, platforms):
        log_messages = []
        try:
            # 1. Data Retrieval
            episode_data_tuple = self.episode_repo.get_episode(episode_id, user_id)
            if not episode_data_tuple or episode_data_tuple[1] != 200:
                log_messages.append(f"Error: Episode {episode_id} not found or access denied for user {user_id}.")
                return {"success": False, "error": "Episode not found or access denied.", "details": log_messages}
            episode = episode_data_tuple[0]
            log_messages.append(f"Fetched episode: {episode.get('title', episode_id)}")

            podcast_id = episode.get('podcast_id')
            if not podcast_id:
                log_messages.append(f"Error: Episode {episode_id} is not linked to a podcast.")
                return {"success": False, "error": "Episode not linked to a podcast.", "details": log_messages}
            
            podcast_data_tuple = self.podcast_repo.get_podcast_by_id(user_id, podcast_id)
            if not podcast_data_tuple or podcast_data_tuple[1] != 200:
                log_messages.append(f"Error: Podcast {podcast_id} not found or access denied for user {user_id}.")
                return {"success": False, "error": "Podcast not found or access denied.", "details": log_messages}
            podcast = podcast_data_tuple[0].get('podcast')
            log_messages.append(f"Fetched podcast: {podcast.get('podName', podcast_id)}")

            # 2. Status Update: Mark as published and set publishDate BEFORE generating RSS
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            update_payload = {
                "status": "published",
                "publishDate": now_utc.isoformat()  # Convert to ISO string
                # Remove 'lastPublishedAt' unless you add it to your schema
            }
            
            current_app.logger.info(f"Attempting to update episode {episode_id} with payload: {update_payload}")
            update_result, update_status = self.episode_repo.update_episode(episode_id, user_id, update_payload)
            
            if update_status == 200:
                log_messages.append(f"Episode status set to 'published' and publishDate to {now_utc.isoformat()} before RSS generation.")
                current_app.logger.info(f"Episode {episode_id} status and publishDate updated successfully.")
            else:
                log_messages.append(f"Warning: Failed to update episode status/publishDate. Status: {update_status}, Result: {update_result}")
                current_app.logger.warning(f"Failed to update episode {episode_id} status/publishDate. Status: {update_status}, Result: {update_result}")
                return {"success": False, "error": "Failed to update episode status for publishing.", "details": log_messages}

            # --- Refactored: Generate and upload RSS feed using RSSService ---
            all_episodes_data, episodes_status_code = self.episode_repo.get_episodes_by_podcast(podcast_id, user_id)
            if episodes_status_code != 200:
                log_messages.append(f"Error: Could not fetch episodes for podcast {podcast_id}.")
                return {"success": False, "error": "Could not fetch episodes for podcast.", "details": log_messages}
            all_episodes_list = all_episodes_data.get("episodes", [])

            # Construct the new proxy URL
            proxy_rss_feed_url = None # Initialize to None
            if direct_rss_blob_url: # Only construct proxy URL if blob upload was successful
                # Use a more robust way to get the base URL of the application
                app_base_url = self.base_url or current_app.config.get('SERVER_NAME') or request.host_url.rstrip('/')
                current_app.logger.info(f"[PublishService] Determined app_base_url: {app_base_url}") # Added log

                if not app_base_url:
                     current_app.logger.warning("Could not determine application base URL for proxy RSS link. Falling back to direct blob URL.")
                     proxy_rss_feed_url = direct_rss_blob_url # Fallback
                else:
                    podcast_name = podcast.get('podName')
                    
                    # Use raw podcast_name as the identifier.
                    # Browsers/clients will URL-encode this if it contains spaces/special chars.
                    # Flask's <path:...> converter will decode it on the server side.
                    if not podcast_name or not podcast_name.strip(): 
                        current_app.logger.warning(
                            f"Podcast name is empty or whitespace for podcast_id '{podcast_id}'. "
                            f"Falling back to podcast_id for proxy URL identifier."
                        )
                        url_identifier = podcast_id 
                    else:
                        url_identifier = podcast_name # Use raw podName
                        
                    proxy_rss_feed_url = f"{app_base_url.rstrip('/')}/rss/{url_identifier}/feed.xml"
                log_messages.append(f"User-facing RSS feed proxy URL: {proxy_rss_feed_url}")
            else:
                # proxy_rss_feed_url remains None if direct_rss_blob_url is None
                log_messages.append("Warning: Direct RSS blob URL not available, so proxy URL cannot be generated for atom:link or frontend.")

            # RSSService generates and uploads the feed.
            # Pass the determined proxy_rss_feed_url to be used as the atom:link self.
            # If proxy_rss_feed_url is None, RSSService might use its own default or the direct blob URL.
            direct_rss_blob_url_from_service = self.rss_service.generate_podcast_rss_feed_and_upload(
                podcast_id=podcast_id,
                user_id=user_id, 
                podcast_details=podcast,
                episodes_list=all_episodes_list,
                atom_link_url=proxy_rss_feed_url, # Pass the generated proxy URL for atom:link
                publishing_episode_id=episode_id
            )

            # Ensure direct_rss_blob_url is updated if it was initially None or if the service returned a new one
            # (though typically it should be the same if already generated, this handles if it was deferred)
            if not direct_rss_blob_url:
                direct_rss_blob_url = direct_rss_blob_url_from_service
            
            if not direct_rss_blob_url:
                 log_messages.append("Critical Error: RSS feed could not be generated or uploaded. Direct blob URL is still None.")
                 # Handle critical failure if direct_rss_blob_url is still None after service call
                 return {"success": False, "error": "RSS feed generation/upload failed critically.", "details": log_messages}


            current_app.logger.info(f"[PublishService] Direct RSS Blob URL from RSSService: {direct_rss_blob_url}") 
            log_messages.append(f"RSS feed generated and uploaded to direct blob URL: {direct_rss_blob_url}")
            
            # If proxy_rss_feed_url couldn't be constructed earlier (e.g. no app_base_url)
            # but direct_rss_blob_url is available, we might decide to not show a proxy URL to the user.
            # The frontend expects rssFeedUrl to be the proxy.
            if not proxy_rss_feed_url and direct_rss_blob_url and app_base_url: # Re-check if app_base_url is now available
                proxy_rss_feed_url = f"{app_base_url.rstrip('/')}/rss/{url_identifier}/feed.xml"
                log_messages.append(f"User-facing RSS feed proxy URL (re-constructed): {proxy_rss_feed_url}")
            elif not proxy_rss_feed_url:
                 log_messages.append("Warning: User-facing proxy RSS URL could not be constructed.")


            current_app.logger.info(f"[PublishService] Final proxy_rss_feed_url to be sent to frontend: {proxy_rss_feed_url}")


            # 4. Platform Processing
            published_to = []
            for platform in platforms:
                platform_lower = platform.lower()
                log_messages.append(f"Processing platform: {platform}")
                if platform_lower == "spotify":
                    log_messages.append("Spotify: RSS feed updated, Spotify will poll automatically.")
                elif platform_lower in ["apple", "google", "amazon", "stitcher", "pocketcasts"]:
                    log_messages.append(f"{platform.capitalize()}: RSS feed updated, platform will poll.")
                else:
                    log_messages.append(f"Platform '{platform}' not specifically implemented; assuming RSS-based.")
                published_to.append(platform)
                time.sleep(0.2)

            # Final update: add platforms
            final_update_payload = {
                "publishedToPlatforms": published_to
            }
            self.episode_repo.update_episode(episode_id, user_id, final_update_payload)
            log_messages.append("Episode platform metadata updated.")

            return {
                "success": True,
                "message": f"Episode '{episode.get('title', episode_id)}' processed for publishing.",
                "details": log_messages,
                "rssFeedUrl": proxy_rss_feed_url # Return the new proxy URL
            }
        except Exception as e:
            current_app.logger.error(f"Unexpected error in publish_episode for {episode_id} by user {user_id}: {str(e)}", exc_info=True)
            log_messages.append(f"Exception: {str(e)}")
            return {
                "success": False,
                "error": f"An unexpected error occurred during publishing: {str(e)}",
                "details": log_messages
            }

    def _get_spotify_access_token(self):
        # Example: Client Credentials Flow
        auth_url = "https://accounts.spotify.com/api/token"
        client_id = self.spotify_client_id
        client_secret = self.spotify_client_secret
        if not client_id or not client_secret:
            raise Exception("Spotify credentials not set in environment variables.")
        response = requests.post(
            auth_url,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        if response.status_code != 200:
            raise Exception(f"Spotify token request failed: {response.text}")
        return response.json()["access_token"]

    def _ping_spotify_rss(self, rss_url, token):
        # Spotify does not have a public API for direct RSS ping, but you can notify via their dashboard or wait for polling.
        # If you have a private endpoint or integration, implement here.
        # Example (pseudo):
        # requests.post("https://api.spotify.com/v1/podcasts/notify", headers={"Authorization": f"Bearer {token}"}, json={"rss_url": rss_url})
        pass

    def _ping_apple_podcasts(self, rss_url):
        # Apple Podcasts does not have a public API for pinging, but you can use their Podcasts Connect dashboard.
        # Optionally, you can try to POST to https://podcastsconnect.apple.com/ or use their API if you have access.
        pass

    def _ping_google_podcasts(self, rss_url):
        # Google Podcasts does not have a public API for pinging, but you can use their Search Console to submit the RSS.
        pass

    def _ping_amazon_music(self, rss_url):
        # Amazon Music does not have a public API for pinging, but you can use their portal to submit the RSS.
        pass

    def _ping_stitcher(self, rss_url):
        # Stitcher does not have a public API for pinging, but you can use their portal to submit the RSS.
        pass

    def _ping_pocketcasts(self, rss_url):
        # Pocket Casts does not have a public API for pinging, but you can use their portal to submit the RSS.
        pass

    def generate_rss_index(feeds):
        """
        Generates an index XML or HTML file listing all podcast RSS feeds.
        'feeds' should be a list of dicts: [{"title": ..., "url": ...}, ...]
        """
        # Example: Generate a simple HTML index
        html = "<html><head><title>Podcast RSS Feeds</title></head><body><h1>All Podcast Feeds</h1><ul>"
        for feed in feeds:
            html += f'<li><a href="{feed["url"]}">{feed["title"]}</a></li>'
        html += "</ul></body></html>"
        return html

    # Usage (not automatic, call as needed):
    # feeds = [{"title": podcast["podName"], "url": f"https://podmanagerstorage.blob.core.windows.net/podmanagerfiles/users/{podcast['ownerId']}/podcasts/{podcast['_id']}/rss/feed.xml"} for podcast in all_podcasts]
    # index_html = generate_rss_index(feeds)
    # Upload index_html to your public /rss/ folder if you want a directory listing.

    def create_sas_upload_url(self, filename, content_type):
        if not self.azure_storage_connection_string or not self.azure_storage_container_name:
            current_app.logger.error("Azure Storage connection string or container name is not configured.")
            raise ValueError("Azure Storage not configured for SAS URL generation.")

        blob_service_client = BlobServiceClient.from_connection_string(self.azure_storage_connection_string)
        # Sanitize filename to prevent path traversal or invalid characters for a blob name segment
        safe_filename_segment = "".join(c if c.isalnum() or c in ['.', '-', '_'] else '_' for c in filename)
        if len(safe_filename_segment) > 100: # Limit length of filename part
            name, ext = os.path.splitext(safe_filename_segment)
            safe_filename_segment = name[:90] + ext

        blob_name = f"uploads/{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{safe_filename_segment}"
        
        account_name = blob_service_client.account_name
        account_key = blob_service_client.credential.account_key
        
        if not account_key:
            current_app.logger.error("Failed to retrieve account key from BlobServiceClient. Check connection string.")
            raise ValueError("Could not retrieve storage account key for SAS token generation.")

        # Ensure generate_blob_sas is called as a standalone function
        # and BlobSasPermissions is used for the permission argument.
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=self.azure_storage_container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(write=True), # Correct usage
            expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            content_type=content_type,
        )
        upload_url = f"https://{account_name}.blob.core.windows.net/{self.azure_storage_container_name}/{blob_name}?{sas_token}"
        blob_url = f"https://{account_name}.blob.core.windows.net/{self.azure_storage_container_name}/{blob_name}"
        return upload_url, blob_url
