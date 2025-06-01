from flask import Blueprint, render_template, request, jsonify, current_app, Response, send_file, g
from backend.services.publishService import PublishService  # Only import the class
from backend.repository.podcast_repository import PodcastRepository # Import PodcastRepository
from bson.objectid import ObjectId
import datetime
from backend.utils.episode_helpers import force_episode_published_status  # Add this import

publish_bp = Blueprint('publish_bp', __name__, url_prefix='/publish')


@publish_bp.route('/', methods=['GET'])
def publish_page():
    """Renders the main publishing page."""
    podcasts_for_template = []
    single_podcast_details = None

    if hasattr(g, "user_id") and g.user_id:
        try:
            podcast_repo = PodcastRepository()
            response, status_code = podcast_repo.get_podcasts(g.user_id)
            if status_code == 200 and response.get("podcast"):
                podcasts_for_template = response["podcast"]
                if len(podcasts_for_template) == 1:
                    single_podcast = podcasts_for_template[0]
                    single_podcast_details = {
                        "id": single_podcast.get("_id"),
                        "name": single_podcast.get("podName")
                    }
        except Exception as e:
            current_app.logger.error(f"Error fetching podcasts for publish page: {e}", exc_info=True)
            # Continue without podcast data if an error occurs

    return render_template(
        'publish/publish.html',
        podcasts=podcasts_for_template, # Pass all podcasts
        single_podcast=single_podcast_details # Pass single podcast details if applicable
    )


@publish_bp.route('/get_sas_url', methods=['POST'])
def get_sas_url():
    data = request.get_json()
    filename = data.get('filename')
    content_type = data.get('contentType')
    if not filename or not content_type:
        return jsonify({"error": "Missing filename or contentType"}), 400

    try:
        # Use a method on PublishService for SAS URL generation
        publish_service = PublishService()
        upload_url, blob_url = publish_service.create_sas_upload_url(filename, content_type)
        return jsonify({"uploadUrl": upload_url, "blobUrl": blob_url})
    except Exception as e:
        current_app.logger.error(f"SAS URL generation failed: {e}")
        return jsonify({"error": "Failed to generate upload URL"}), 500


@publish_bp.route('/publish_episode', methods=['POST'])
def publish_episode():
    data = request.get_json()
    required_fields = ['title', 'description', 'episodeNumber', 'seasonNumber', 'explicit', 'audioUrl', 'publishDate']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    try:
        # Validate publishDate
        publish_date = datetime.datetime.fromisoformat(data['publishDate'].replace('Z', '+00:00'))
        episode_id = save_episode_to_db(data, publish_date)
        trigger_encoding_job(episode_id)

        # Optionally notify directories immediately or schedule
        notify_spotify(episode_id)
        notify_youtube_podcasts(episode_id)  # Fixed the extra parenthesis

        return jsonify({"message": "Episode saved and encoding triggered", "episodeId": str(episode_id)})
    except Exception as e:
        current_app.logger.error(f"Episode publish failed: {e}")
        return jsonify({"error": "Failed to publish episode"}), 500


@publish_bp.route('/rss/<podcast_id>.xml', methods=['GET'])
def rss_feed(podcast_id):
    try:
        rss_xml = generate_rss_feed(podcast_id)
        return Response(rss_xml, mimetype='application/rss+xml')
    except Exception as e:
        current_app.logger.error(f"RSS feed generation failed: {e}")
        return jsonify({"error": "Failed to generate RSS feed"}), 500


@publish_bp.route('/download/<episode_id>', methods=['GET'])
def download_proxy(episode_id):
    try:
        record_download(episode_id)
        stream = get_episode_audio_stream(episode_id)
        return send_file(stream, mimetype='audio/mpeg', as_attachment=False)
    except Exception as e:
        current_app.logger.error(f"Download failed: {e}")
        return jsonify({"error": "Failed to download episode"}), 500


@publish_bp.route('/api/publish_episode/<episode_id>', methods=['POST'])
def api_publish_episode(episode_id):
    """
    API endpoint to initiate the publishing process for an episode.
    Expects a JSON payload with 'platforms' (list) and optional 'notes' (string).
    """
    if not hasattr(g, "user_id") or not g.user_id:
        current_app.logger.warning(f"Unauthorized attempt to publish episode {episode_id}: No user_id in g")
        return jsonify({"success": False, "error": "User not authenticated"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON payload"}), 400

        platforms = data.get('platforms')

        if not episode_id:
            return jsonify({"success": False, "error": "Episode ID is required"}), 400
        if not platforms or not isinstance(platforms, list):
            return jsonify({"success": False, "error": "Platforms list is required"}), 400

        current_app.logger.info(f"Publish request for episode {episode_id} by user {g.user_id} to platforms: {platforms}.")
        
        publish_service = PublishService()
        result = publish_service.publish_episode(episode_id, g.user_id, platforms)
        
        # Add a failsafe to ensure published status
        if result.get("success"):
            # Double-check episode status after successful publish
            episode_data, _ = publish_service.episode_repo.get_episode(episode_id, g.user_id)
            if episode_data and episode_data.get("status", "").lower() != "published":
                current_app.logger.warning(f"Episode {episode_id} status is not 'published' after successful publish. Forcing status update.")
                force_published = force_episode_published_status(episode_id, g.user_id)
                current_app.logger.info(f"Force update result: {force_published}")
                result["details"].append(f"Status force-updated: {force_published}")
                
            return jsonify(result), 200
        else:
            return jsonify(result), 500 

    except Exception as e:
        current_app.logger.error(f"Error in api_publish_episode for episode {episode_id}: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"An unexpected error occurred: {str(e)}"}), 500

# Replace this function if it exists
def notify_youtube_podcasts(episode_id):
    # YouTube Podcasts does not have a public API for pinging, but you can use their directory to submit the RSS.
    pass
