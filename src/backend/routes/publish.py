from flask import Blueprint, render_template, request, jsonify, current_app, Response, send_file
from backend.services.publishService import ( # Corrected import path
    create_sas_upload_url,
    save_episode_to_db,
    trigger_encoding_job,
    generate_rss_feed,
    record_download,
    notify_spotify,
    notify_google_podcasts,
    get_episode_audio_stream
)
from bson.objectid import ObjectId
import datetime

publish_bp = Blueprint('publish_bp', __name__, url_prefix='/publish')


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
        upload_url, blob_url = create_sas_upload_url(filename, content_type)
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
        notify_google_podcasts(episode_id)

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
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON payload"}), 400

        platforms = data.get('platforms')
        notes = data.get('notes', '')

        if not episode_id:
            return jsonify({"success": False, "error": "Episode ID is required"}), 400
        if not platforms or not isinstance(platforms, list):
            return jsonify({"success": False, "error": "Platforms list is required"}), 400

        current_app.logger.info(f"Publish request for episode {episode_id} to platforms: {platforms}. Notes: {notes}")
        
        publish_service = PublishService()
        result = publish_service.publish_episode(episode_id, platforms, notes)

        if result.get("success"):
            # Here you might also want to update the episode's status in the database
            # e.g., episode_repo.update_episode_status(episode_id, "Published")
            return jsonify(result), 200
        else:
            return jsonify(result), 500 # Or a more specific error code based on result

    except Exception as e:
        current_app.logger.error(f"Error in api_publish_episode for episode {episode_id}: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"An unexpected error occurred: {str(e)}"}), 500
