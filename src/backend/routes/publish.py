from flask import Blueprint, render_template, request, jsonify, current_app, Response, send_file, g # Added g
# Removed problematic imports:
# save_episode_to_db, trigger_encoding_job, generate_rss_feed,
# record_download, notify_spotify, notify_google_podcasts, get_episode_audio_stream
# are not standalone functions in publishService.py.
from backend.services.publishService import PublishService # Ensure PublishService class is imported
from bson.objectid import ObjectId
import datetime

publish_bp = Blueprint('publish_bp', __name__, url_prefix='/publish')
# Create an instance of PublishService to use its methods
publish_service_instance = PublishService() 

@publish_bp.route('/', methods=['GET'])
def publish_page():
    """Renders the main publishing page."""
    return render_template('publish/publish.html')


@publish_bp.route('/get_sas_url', methods=['POST'])
def get_sas_url():
    data = request.get_json()
    filename = data.get('filename')
    content_type = data.get('contentType')
    if not filename or not content_type:
        return jsonify({"error": "Missing filename or contentType"}), 400

    try:
        # Call create_sas_upload_url as a method of the PublishService instance
        upload_url, blob_url = publish_service_instance.create_sas_upload_url(filename, content_type)
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
        
        # The following functions will now cause NameError as they are not defined/imported:
        # episode_id = save_episode_to_db(data, publish_date) 
        # trigger_encoding_job(episode_id)
        # notify_spotify(episode_id)
        # notify_google_podcasts(episode_id)
        # This route needs to be refactored to use appropriate service methods or repository methods.
        # For now, to proceed past the ImportError, we acknowledge these will be NameErrors.
        # Placeholder for demonstration; actual implementation needed:
        current_app.logger.warning("Route /publish_episode is calling undefined functions: save_episode_to_db, trigger_encoding_job, etc.")
        episode_id = "mock_episode_id_from_old_route" # Placeholder

        return jsonify({"message": "Episode (mock) saved and encoding (mock) triggered", "episodeId": str(episode_id)})
    except Exception as e:
        current_app.logger.error(f"Episode publish failed: {e}")
        return jsonify({"error": "Failed to publish episode"}), 500


@publish_bp.route('/rss/<podcast_id>.xml', methods=['GET'])
def rss_feed(podcast_id):
    try:
        # generate_rss_feed will cause NameError
        # rss_xml = generate_rss_feed(podcast_id)
        # This route needs refactoring. For now, return placeholder.
        current_app.logger.warning("Route /rss/<podcast_id>.xml is calling undefined function: generate_rss_feed")
        rss_xml = "<error>RSS generation logic not implemented for this route.</error>"
        return Response(rss_xml, mimetype='application/rss+xml')
    except Exception as e:
        current_app.logger.error(f"RSS feed generation failed: {e}")
        return jsonify({"error": "Failed to generate RSS feed"}), 500


@publish_bp.route('/download/<episode_id>', methods=['GET'])
def download_proxy(episode_id):
    try:
        # record_download and get_episode_audio_stream will cause NameError
        # record_download(episode_id)
        # stream = get_episode_audio_stream(episode_id)
        # This route needs refactoring. For now, return placeholder.
        current_app.logger.warning("Route /download/<episode_id> is calling undefined functions: record_download, get_episode_audio_stream")
        return jsonify({"error": "Download logic not implemented for this route"}), 501 # Not Implemented
    except Exception as e:
        current_app.logger.error(f"Download failed: {e}")
        return jsonify({"error": "Failed to download episode"}), 500


@publish_bp.route('/api/publish_episode/<episode_id>', methods=['POST'])
def api_publish_episode(episode_id):
    """
    API endpoint to initiate the publishing process for an episode.
    Expects a JSON payload with 'platforms' (list) and optional 'notes' (string).
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON payload"}), 400

        platforms = data.get('platforms')
        # The 'notes' parameter was expected by publish_service.publish_episode before,
        # but the method signature in PublishService is publish_episode(self, episode_id, user_id, platforms)
        # Assuming user_id should be g.user_id and notes is not used by the service method.
        # For now, let's assume g.user_id is the intended user_id.
        user_id = getattr(g, 'user_id', None)
        if not user_id:
             return jsonify({"success": False, "error": "User not authenticated"}), 401


        if not episode_id:
            return jsonify({"success": False, "error": "Episode ID is required"}), 400
        if not platforms or not isinstance(platforms, list):
            return jsonify({"success": False, "error": "Platforms list is required"}), 400

        current_app.logger.info(f"Publish request for episode {episode_id} to platforms: {platforms}. User: {user_id}")
        
        # Use the module-level instance or create a new one
        # publish_service = PublishService() # This was here, can use publish_service_instance
        result = publish_service_instance.publish_episode(episode_id, user_id, platforms)

        if result.get("success"):
            # Here you might also want to update the episode's status in the database
            # e.g., episode_repo.update_episode_status(episode_id, "Published")
            return jsonify(result), 200
        else:
            return jsonify(result), 500 # Or a more specific error code based on result

    except Exception as e:
        current_app.logger.error(f"Error in api_publish_episode for episode {episode_id}: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"An unexpected error occurred: {str(e)}"}), 500
