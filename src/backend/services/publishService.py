import os
import datetime
import requests
import time  # This is already imported globally
from flask import current_app
from backend.repository.episode_repository import EpisodeRepository
from backend.repository.podcast_repository import PodcastRepository
from azure.storage.blob import BlobServiceClient

class PublishService:
    def __init__(self):
        self.episode_repo = EpisodeRepository()
        self.podcast_repo = PodcastRepository()
        # Load credentials from environment
        self.spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.spotify_refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
        self.rss_feed_base_url = os.getenv("RSS_FEED_BASE_URL")  
        self.azure_conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        # Use a default if env var is missing
        self.rss_blob_container = os.getenv("AZURE_STORAGE_CONTAINER_NAME") or "podmanagerfiles"

    def publish_episode(self, episode_id, user_id, platforms):
        log_messages = []
        try:
            # 1. Data Retrieval (episode and podcast details)
            episode_data_tuple = self.episode_repo.get_episode(episode_id, user_id)
            if not episode_data_tuple or episode_data_tuple[1] != 200:
                return {"success": False, "error": "Episode not found or access denied.", "details": log_messages}
            episode = episode_data_tuple[0]
            log_messages.append(f"Fetched episode: {episode.get('title', episode_id)}")

            podcast_id = episode.get('podcast_id')
            if not podcast_id:
                return {"success": False, "error": "Episode not linked to a podcast.", "details": log_messages}
            podcast_data_tuple = self.podcast_repo.get_podcast_by_id(user_id, podcast_id)
            if not podcast_data_tuple or podcast_data_tuple[1] != 200:
                return {"success": False, "error": "Podcast not found or access denied.", "details": log_messages}
            podcast = podcast_data_tuple[0].get('podcast')
            log_messages.append(f"Fetched podcast: {podcast.get('podName', podcast_id)}")

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
                time.sleep(0.2)  # Using global time module

            # CRITICAL FIX: Update Episode Status in Database 
            intended_status_for_published_episode = "published"  # Important: keep lowercase
            update_payload = {
                "status": intended_status_for_published_episode,
                "publishedToPlatforms": published_to,
                "lastPublishedAt": datetime.datetime.utcnow()
            }
            
            # Force direct update to the Episodes collection to ensure status is properly set
            current_app.logger.info(f"DIRECT DB UPDATE: Setting episode {episode_id} status to '{intended_status_for_published_episode}' in database")
            from backend.database.mongo_connection import collection
            episodes_collection = collection.database.Episodes
            
            # First attempt - direct MongoDB update
            direct_update = episodes_collection.update_one(
                {"_id": episode_id, "userid": str(user_id)},
                {"$set": {
                    "status": intended_status_for_published_episode,
                    "publishedToPlatforms": published_to,
                    "lastPublishedAt": datetime.datetime.utcnow()
                }}
            )
            
            log_messages.append(f"Direct MongoDB update result: matched={direct_update.matched_count}, modified={direct_update.modified_count}")
            
            # Second attempt - use repository method
            update_result, update_status_code = self.episode_repo.update_episode(
                episode_id, user_id, update_payload
            )
            
            # Verify the update immediately
            verify_episode = episodes_collection.find_one({"_id": episode_id})
            if verify_episode:
                current_status = verify_episode.get("status", "unknown")
                log_messages.append(f"Episode status after updates: {current_status}")
                if current_status != intended_status_for_published_episode:
                    # Third attempt - final forced update if still not published
                    emergency_update = episodes_collection.update_one(
                        {"_id": episode_id},
                        {"$set": {"status": intended_status_for_published_episode}}
                    )
                    log_messages.append(f"Emergency status update: matched={emergency_update.matched_count}, modified={emergency_update.modified_count}")
            
            # ...existing code for RSS generation...

            # When generating RSS, ALWAYS use the intended_status_for_published_episode
            rss_xml = self._generate_rss_feed_xml(
                podcast_id,
                podcast,
                user_id,
                episode_id_being_published=episode_id,
                status_of_episode_being_published=intended_status_for_published_episode  # Always force published status
            )
            
            # ...existing code...

            # 4. Upload RSS feed to Blob Storage
            current_app.logger.info(f"Uploading RSS feed to blob storage for podcast {podcast_id}")
            rss_blob_url = self._upload_rss_to_blob(podcast_id, rss_xml, user_id)
            log_messages.append(f"RSS feed uploaded to {rss_blob_url}")
            
            # Final verification - fetch and parse the uploaded RSS to confirm episode is there
            try:
                import requests
                rss_response = requests.get(rss_blob_url, timeout=10)
                if rss_response.status_code == 200 and episode.get('title') and episode['title'] in rss_response.text:
                    log_messages.append(f"FINAL VERIFICATION: Episode '{episode['title']}' confirmed in uploaded RSS feed at {rss_blob_url}")
                else:
                    log_messages.append(f"FINAL VERIFICATION FAILED: Episode not found in uploaded RSS feed")
            except Exception as verify_error:
                log_messages.append(f"Could not verify uploaded RSS feed: {verify_error}")

            return {
                "success": True,
                "message": f"Episode '{episode.get('title', episode_id)}' processed for publishing.",
                "details": log_messages,
                "rssFeedUrl": rss_blob_url
            }
        except Exception as e:
            log_messages.append(f"Exception during publish_episode: {str(e)}")
            current_app.logger.error(f"Exception in publish_episode for {episode_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"An unexpected error occurred during publishing: {str(e)}",
                "details": log_messages
            }

    def _generate_rss_feed_xml(self, podcast_id, podcast, user_id, episode_id_being_published=None, status_of_episode_being_published=None):
        episodes_for_rss_map = {}

        # 1. Handle the episode that was targeted by the publish action
        if episode_id_being_published:
            current_app.logger.info(f"RSS: Processing specific episode_id_being_published: {episode_id_being_published}, with intended status for this RSS generation: {status_of_episode_being_published}")
            ep_data_tuple = self.episode_repo.get_episode(episode_id_being_published, user_id)
            if ep_data_tuple and ep_data_tuple[1] == 200:
                episode_obj = ep_data_tuple[0]
                original_status = episode_obj.get('status', 'NO_STATUS')
                if status_of_episode_being_published:
                    episode_obj['status'] = status_of_episode_being_published.lower()
                    current_app.logger.info(f"RSS: Forcing status of {episode_id_being_published} from '{original_status}' to '{episode_obj['status']}' for this RSS generation due to successful publish call.")
                else:
                    current_app.logger.info(f"RSS: Using DB status '{episode_obj.get('status')}' for {episode_id_being_published} as status_of_episode_being_published was None (e.g. DB update failed or general RSS regen).")
                episodes_for_rss_map[episode_id_being_published] = episode_obj
                current_app.logger.info(f"RSS: Added episode {episode_id_being_published} to RSS map with status '{episode_obj['status']}'")
            else:
                current_app.logger.warning(f"RSS: Could not fetch specific episode {episode_id_being_published}. It will be missing from the feed if not also in the general list.")

        # 2. Fetch all episodes for the podcast
        all_episodes_data, _ = self.episode_repo.get_episodes_by_podcast(podcast_id, user_id)
        for ep_from_list in all_episodes_data.get("episodes", []):
            ep_id = ep_from_list.get("_id")
            if ep_id not in episodes_for_rss_map:
                episodes_for_rss_map[ep_id] = ep_from_list
                current_app.logger.debug(f"RSS: Added episode {ep_id} from podcast list with status '{ep_from_list.get('status')}'")

        final_episodes_list = list(episodes_for_rss_map.values())
        current_app.logger.info(f"RSS: Total episodes in map before filtering: {len(final_episodes_list)}")

        # Log all episodes before filtering
        for ep in final_episodes_list:
            current_app.logger.info(f"RSS: Episode in list - ID: {ep.get('_id')}, Title: '{ep.get('title')}', Status: '{ep.get('status')}'")

        # Fix the sort function to handle None values safely
        def safe_sort_key(ep):
            publish_date = ep.get('publishDate')
            if not publish_date:
                return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
                
            if isinstance(publish_date, str):
                try:
                    dt = datetime.datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=datetime.timezone.utc)
                    return dt
                except ValueError:
                    return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
            
            if isinstance(publish_date, datetime.datetime):
                if publish_date.tzinfo is None:
                    publish_date = publish_date.replace(tzinfo=datetime.timezone.utc)
                return publish_date
                
            return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
            
        # Replace the lambda sort with our safe sort function
        final_episodes_list.sort(key=safe_sort_key, reverse=True)
        current_app.logger.info(f"RSS: Total episodes prepared for feed generation: {len(final_episodes_list)}")

        from email.utils import format_datetime

        def format_duration(seconds):
            if not seconds or not isinstance(seconds, (int, float)) or seconds < 0:
                return "00:00:00"
            try:
                seconds = int(seconds)
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                secs = seconds % 60
                return f"{hours:02}:{minutes:02}:{secs:02}"
            except:
                return "00:00:00"

        items_xml = ""
        published_episodes_count = 0
        for ep_idx, ep in enumerate(final_episodes_list):
            current_ep_status_for_rss = ep.get("status", "").lower()
            current_app.logger.debug(f"RSS item check [{ep_idx}]: ID {ep.get('_id')}, Title '{ep.get('title', 'N/A')}', Status for RSS '{current_ep_status_for_rss}'")
            if current_ep_status_for_rss == "published":
                published_episodes_count += 1
                current_app.logger.info(f"RSS: Including episode {ep.get('_id')} - '{ep.get('title')}' in RSS feed (status: {current_ep_status_for_rss})")
                pub_date_str = ""
                try:
                    pub_date_obj = ep.get('publishDate')
                    if isinstance(pub_date_obj, str):
                        pub_date_obj = datetime.datetime.fromisoformat(pub_date_obj.replace('Z', '+00:00'))
                    if isinstance(pub_date_obj, datetime.datetime):
                        if pub_date_obj.tzinfo is None:
                            pub_date_obj = pub_date_obj.replace(tzinfo=datetime.timezone.utc)
                        pub_date_str = format_datetime(pub_date_obj)
                except Exception as e:
                    current_app.logger.error(f"Error formatting pubDate for episode {ep.get('_id')}: {e}")

                episode_image = ep.get('imageUrl', podcast.get('logoUrl', ''))
                episode_keywords = ", ".join(ep.get('keywords', [])) if ep.get('keywords') else ""

                items_xml += f"""
                <item>
                    <title><![CDATA[{ep.get('title', 'No Title')}]]></title>
                    <description><![CDATA[{ep.get('description', '')}]]></description>
                    <itunes:summary><![CDATA[{ep.get('summary', ep.get('description', ''))}]]></itunes:summary>
                    <itunes:subtitle><![CDATA[{ep.get('subtitle', '')}]]></itunes:subtitle>
                    <enclosure url="{ep.get('audioUrl', '')}" length="{ep.get('fileSize', 0) or 0}" type="{ep.get('fileType', 'audio/mpeg')}" />
                    <guid isPermaLink="false">{ep.get('_id', '')}</guid>
                    <pubDate>{pub_date_str}</pubDate>
                    <itunes:duration>{format_duration(ep.get('duration'))}</itunes:duration>
                    <itunes:explicit>{"yes" if ep.get('explicit') else "no"}</itunes:explicit>
                    <itunes:episode>{ep.get('episode', '')}</itunes:episode>
                    <itunes:season>{ep.get('season', '')}</itunes:season>
                    <itunes:episodeType>{ep.get('episodeType', 'full')}</itunes:episodeType>
                    {f'<itunes:image href="{episode_image}" />' if episode_image else ''}
                    {f'<link>{ep.get("link", "")}</link>' if ep.get("link") else ''}
                    {f'<itunes:keywords>{episode_keywords}</itunes:keywords>' if episode_keywords else ''}
                    <itunes:author><![CDATA[{ep.get('author', podcast.get('author', podcast.get('ownerName', '')))}]]></itunes:author>
                </item>
                """
            else:
                current_app.logger.debug(f"RSS: Excluding episode {ep.get('_id')} - '{ep.get('title')}' from RSS feed (status: {current_ep_status_for_rss})")

        current_app.logger.info(f"RSS: Total published episodes included in RSS feed: {published_episodes_count}")

        # Podcast categories
        categories_xml = ""
        podcast_categories = podcast.get('category')
        if isinstance(podcast_categories, str) and podcast_categories:
            categories_xml += f'<itunes:category text="{podcast_categories.strip()}" />\n'
        elif isinstance(podcast_categories, list):
            for cat_obj in podcast_categories:
                if isinstance(cat_obj, dict) and cat_obj.get('text'):
                    main_cat_text = cat_obj['text'].strip()
                    sub_cat_xml = ""
                    if cat_obj.get('subcategory') and isinstance(cat_obj['subcategory'], dict) and cat_obj['subcategory'].get('text'):
                        sub_cat_text = cat_obj['subcategory']['text'].strip()
                        sub_cat_xml = f'<itunes:category text="{sub_cat_text}" />'
                    categories_xml += f'<itunes:category text="{main_cat_text}">{sub_cat_xml}</itunes:category>\n'

        # Construct the full RSS feed URL for atom:link
        full_feed_url = ""
        if self.rss_feed_base_url:
            full_feed_url = self.rss_feed_base_url.replace("<g.user_id>", str(user_id)).replace("<podcast_id>", str(podcast_id)) + "feed.xml"

        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0"
             xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
             xmlns:content="http://purl.org/rss/1.0/modules/content/"
             xmlns:atom="http://www.w3.org/2005/Atom">
        <channel>
            <title><![CDATA[{podcast.get('podName', 'No Podcast Title')}]]></title>
            <link>{podcast.get('podUrl', '')}</link>
            <description><![CDATA[{podcast.get('description', '')}]]></description>
            <language>{podcast.get('language', 'en-us')}</language>
            <copyright><![CDATA[{podcast.get('copyright_info', f'© {datetime.datetime.now().year} {podcast.get("ownerName", "")}')}]]></copyright>
            <lastBuildDate>{format_datetime(datetime.datetime.now(datetime.timezone.utc))}</lastBuildDate>
            {f'<atom:link href="{full_feed_url}" rel="self" type="application/rss+xml" />' if full_feed_url else ''}
            <itunes:author><![CDATA[{podcast.get('author', podcast.get('ownerName', ''))}]]></itunes:author>
            <itunes:summary><![CDATA[{podcast.get('description', '')}]]></itunes:summary>
            <itunes:type>{podcast.get('itunes_type', 'episodic')}</itunes:type>
            <itunes:owner>
                <itunes:name><![CDATA[{podcast.get('ownerName', '')}]]></itunes:name>
                <itunes:email>{podcast.get('email', '')}</itunes:email>
            </itunes:owner>
            {f'<itunes:image href="{podcast.get("logoUrl", "")}" />' if podcast.get("logoUrl") else ''}
            <itunes:explicit>{"yes" if podcast.get('explicit') else "no"}</itunes:explicit>
            {categories_xml}
            {items_xml}
        </channel>
        </rss>
        """
        return rss_xml.strip()

    def _upload_rss_to_blob(self, podcast_id, rss_xml, user_id=None):
        """
        Uploads the RSS XML to Azure Blob Storage at the path matching RSS_FEED_BASE_URL.
        """
        blob_service_client = BlobServiceClient.from_connection_string(self.azure_conn_str)
        if not user_id:
            raise Exception("user_id is required to build the RSS blob path.")
        
        # The blob_path should be relative to the container.
        blob_path = f"users/{user_id}/podcasts/{podcast_id}/rss/feed.xml"
        container_name = self.rss_blob_container

        # ADD: Check for missing container name
        if not container_name:
            raise Exception("AZURE_STORAGE_CONTAINER_NAME is not set in environment variables.")

        current_app.logger.info(f"Attempting to upload RSS to container: '{container_name}', blob path: '{blob_path}'")

        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
        blob_client.upload_blob(rss_xml, overwrite=True, content_type="application/rss+xml")
        
        # Dynamically construct the public URL by replacing placeholders in RSS_FEED_BASE_URL
        # Ensure RSS_FEED_BASE_URL is correctly defined, e.g.,
        # https://<ACCOUNT_NAME>.blob.core.windows.net/<CONTAINER_NAME>/users/<g.user_id>/podcasts/<podcast_id>/
        # The feed_url should then append "feed.xml" to this base.
        
        # The existing logic for feed_url construction seems to assume RSS_FEED_BASE_URL
        # already includes the account and container, and ends just before the user/podcast part.
        # Example: RSS_FEED_BASE_URL="https://podmanagerstorage.blob.core.windows.net/podmanagerfiles/"
        # Then the path part would be "users/<g.user_id>/podcasts/<podcast_id>/feed.xml"
        # Let's adjust the feed_url construction to be more robust if RSS_FEED_BASE_URL might vary.

        # Assuming RSS_FEED_BASE_URL is like: "https://<ACCOUNT_NAME>.blob.core.windows.net/<CONTAINER_NAME>/"
        # And the blob_path is "users/.../feed.xml"
        # A more direct construction of the public URL:
        account_name = blob_service_client.account_name
        public_url_base = f"https://{account_name}.blob.core.windows.net/{container_name}/"
        
        feed_url = public_url_base + blob_path # blob_path already includes "users/.../feed.xml"

        # If your RSS_FEED_BASE_URL is already structured to include the dynamic parts,
        # the original replacement logic is fine, but ensure it's correct.
        # For now, using the direct construction above for clarity.
        # If you revert, ensure RSS_FEED_BASE_URL is like:
        # "https://podmanagerstorage.blob.core.windows.net/podmanagerfiles/users/<g.user_id>/podcasts/<podcast_id>/"
        # and then:
        # feed_url = self.rss_feed_base_url.replace("<g.user_id>", str(user_id)).replace("<podcast_id>", str(podcast_id)) + "feed.xml"
        # This original logic is likely correct if RSS_FEED_BASE_URL is set up as expected.
        # Let's stick to the original logic for feed_url if RSS_FEED_BASE_URL is correctly defined.
        
        # Reverting to original feed_url logic, assuming RSS_FEED_BASE_URL is correctly set up.
        # Ensure RSS_FEED_BASE_URL = "https://podmanagerstorage.blob.core.windows.net/podmanagerfiles/users/<g.user_id>/podcasts/<podcast_id>/"
        if not self.rss_feed_base_url:
            current_app.logger.error("RSS_FEED_BASE_URL is not set in environment variables.")
            raise Exception("RSS_FEED_BASE_URL is not configured.")
            
        feed_url = self.rss_feed_base_url.replace("<g.user_id>", str(user_id)).replace("<podcast_id>", str(podcast_id)) + "feed.xml"
        current_app.logger.info(f"RSS feed URL generated: {feed_url}")
        return feed_url

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
        blob_service_client = BlobServiceClient.from_connection_string(self.azure_conn_str)
        blob_name = f"uploads/{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
        sas_token = blob_service_client.generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=self.rss_blob_container,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission="w",
            expiry=datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
            content_type=content_type,
        )
        upload_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{self.rss_blob_container}/{blob_name}?{sas_token}"
        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{self.rss_blob_container}/{blob_name}"
        return upload_url, blob_url
