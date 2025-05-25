import os
import logging
import requests
from colorama import init
from flask import Flask, jsonify, request, session, g, Response, current_app
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from backend.database.mongo_connection import mongo 
from backend.services.publishService import PublishService # Import PublishService

# Import blueprints
from backend.routes.publish import publish_bp
from backend.routes.auth import auth_bp
from backend.routes.podcast import podcast_bp
from backend.routes.dashboard import dashboard_bp
from backend.routes.pod_management import pod_management_bp
from backend.routes.podtask import podtask_bp
from backend.routes.account import account_bp
from backend.routes.credits_routes import credits_bp
from backend.routes.team import team_bp
from backend.routes.guest import guest_bp
from backend.routes.user_to_team import usertoteam_bp
from backend.routes.invitation import invitation_bp
from backend.routes.google_calendar import google_calendar_bp
from backend.routes.episode import episode_bp
from backend.routes.podprofile import podprofile_bp
from backend.routes.activation import activation_bp, podprofile_initial_bp
from backend.routes.frontend import frontend_bp
from backend.routes.guestpage import guestpage_bp
from backend.routes.guest_to_eposide import guesttoepisode_bp
from backend.routes.guest_form import guest_form_bp
from backend.routes.billing import billing_bp
from backend.routes.landingpage import landingpage_bp
from backend.routes.Mailing_list import Mailing_list_bp
from backend.routes.user import user_bp
from backend.routes.audio_routes import audio_bp
from backend.routes.video_routes import video_bp
from backend.routes.transcription import transcription_bp
from backend.routes.comment import comment_bp
from backend.routes.activity import activity_bp
from backend.routes.stripe_config import stripe_config_bp
from backend.routes.edit_routes import edit_bp
from backend.routes.enterprise import enterprise_bp
from backend.routes.lia import lia_bp
from backend.routes.index import index_bp
from backend.routes.recording_studio import register_socketio_events  # <- updated import
from backend.routes.recording_studio import recording_studio_bp

# Utils
from backend.utils.scheduler import start_scheduler
from backend.utils.credit_scheduler import init_credit_scheduler
from backend.utils import venvupdate

# Start environment setup
if os.getenv("SKIP_VENV_UPDATE", "false").lower() not in ("true", "1", "yes"):
    venvupdate.update_venv_and_requirements()

load_dotenv()

template_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "frontend", "templates")
static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "frontend", "static")

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
socketio = SocketIO(app, cors_allowed_origins="*")  # Create instance

CORS(app, resources={r"/*": {"origins": [
    "https://devapp.podmanager.ai",
    "https://app.podmanager.ai",
    "http://127.0.0.1:8000",
]}})

app.secret_key = os.getenv("SECRET_KEY")
app.config["PREFERRED_URL_SCHEME"] = "https"

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(podcast_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(pod_management_bp)
app.register_blueprint(podtask_bp)
app.register_blueprint(team_bp)
app.register_blueprint(Mailing_list_bp)
app.register_blueprint(guest_bp)
app.register_blueprint(guestpage_bp)
app.register_blueprint(account_bp)
app.register_blueprint(credits_bp)
app.register_blueprint(usertoteam_bp)
app.register_blueprint(invitation_bp)
app.register_blueprint(google_calendar_bp)
app.register_blueprint(episode_bp)
app.register_blueprint(podprofile_bp)
app.register_blueprint(activation_bp, url_prefix='/activation')
app.register_blueprint(podprofile_initial_bp, url_prefix='/podprofile')
app.register_blueprint(frontend_bp)
app.register_blueprint(guesttoepisode_bp)
app.register_blueprint(transcription_bp, url_prefix="/transcription")
app.register_blueprint(audio_bp)
app.register_blueprint(video_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(guest_form_bp, url_prefix="/guest-form")
app.register_blueprint(user_bp, url_prefix="/user")
app.register_blueprint(landingpage_bp)
app.register_blueprint(comment_bp)
app.register_blueprint(activity_bp)
app.register_blueprint(stripe_config_bp)
app.register_blueprint(edit_bp)
app.register_blueprint(enterprise_bp, url_prefix="/enterprise")
app.register_blueprint(lia_bp, url_prefix="/lia")
app.register_blueprint(index_bp)
app.register_blueprint(recording_studio_bp)
app.register_blueprint(publish_bp, url_prefix='/publish') # Register the publish blueprint

# Set up environment and logging
APP_ENV = os.getenv("APP_ENV", "production")
API_BASE_URL = os.getenv("API_BASE_URL")

init(autoreset=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("========================================")
logger.info("✓ Starting server...")
logger.info(f"API Base URL: {API_BASE_URL}")
logger.info(f"MongoDB URI:  {os.getenv('MONGODB_URI')}")
logger.info("========================================")
logger.info("📧 Email Configuration:")
logger.info(f"EMAIL_USER: {os.getenv('EMAIL_USER', 'Not Set')}")
logger.info(f"EMAIL_PASS: {'**** **** **** ****' if os.getenv('EMAIL_PASS') else 'Not Set'}")
logger.info("========================================")
logger.info("🚀 Server is running!")
logger.info(f"🌐 Local:  {os.getenv('LOCAL_BASE_URL', 'http://127.0.0.1:8000')}")

api_base_url_for_network = os.getenv('API_BASE_URL', 'Not Set')
if ':' not in api_base_url_for_network.split('//')[-1]:
    api_base_url_for_network += ':8000'
logger.info(f"🌐 Network: {api_base_url_for_network}")
logger.info("========================================")

@app.before_request
def load_user():
    logger.info(f"Session object before loading user: {dict(session)}")
    g.user_id = session.get("user_id")
    logger.info(f"Request to {request.path} by user {g.user_id if g.user_id else 'None'}")

# Initialize schedulers
start_scheduler(app)
init_credit_scheduler(app)

# 🔌 Register socket events
register_socketio_events(socketio)

@app.route('/rss/<path:podcast_identifier>/feed.xml') # Changed from <slug> to <path:podcast_identifier>
def rss_feed_proxy(podcast_identifier):
    # podcast_identifier here will be URL-decoded by Flask's path converter.
    current_app.logger.info(f"RSS proxy request for identifier: '{podcast_identifier}'")
    
    publish_service_instance = PublishService() # Instantiate PublishService
    podcast_id, user_id = publish_service_instance._find_podcast_details_by_identifier(podcast_identifier)

    if not podcast_id or not user_id:
        current_app.logger.error(f"Could not find podcast or user for identifier: '{podcast_identifier}'")
        return jsonify({"error": "Podcast not found or identifier invalid"}), 404

    # Construct the direct blob URL for the RSS feed
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME") # This should be the container for RSS files
    
    if not account_name or not container_name:
        current_app.logger.error("Azure Storage account name or container name not configured for RSS proxy.")
        return jsonify({"error": "Server configuration error for RSS feed"}), 500

    # Path structure for RSS feed in blob storage
    blob_name = f"users/{user_id}/podcasts/{podcast_id}/rss/feed.xml"
    direct_rss_blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}"
    current_app.logger.info(f"Proxying RSS feed. Identifier: '{podcast_identifier}', Mapped to PodcastID: {podcast_id}, UserID: {user_id}, Blob URL: {direct_rss_blob_url}")

    try:
        # Fetch the RSS feed from Azure Blob Storage
        # Using a new BlobServiceClient instance for this request.
        # Consider if a shared client or connection pool is better for high traffic.
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            current_app.logger.error("Azure Storage connection string not configured.")
            return jsonify({"error": "Server configuration error for RSS feed access"}), 500

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        if not blob_client.exists():
            current_app.logger.error(f"RSS feed blob not found at {direct_rss_blob_url}")
            return jsonify({"error": "RSS feed not found"}), 404

        downloader = blob_client.download_blob()
        rss_content = downloader.readall()
        
        # Serve the content with the correct MIME type
        return Response(rss_content, mimetype='application/rss+xml')

    except Exception as e:
        current_app.logger.error(f"Error proxying RSS feed for identifier '{podcast_identifier}': {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve RSS feed"}), 500

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)