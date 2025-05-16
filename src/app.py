import os
import logging  # Ensure logging is imported
from colorama import init # Add this line
from flask import Flask, request, session, g, jsonify, render_template
from flask_cors import CORS
from backend.routes.auth import auth_bp
from backend.routes.podcast import podcast_bp  # Import the podcast blueprint
from backend.routes.dashboard import dashboard_bp
from backend.routes.pod_management import pod_management_bp
from backend.routes.podtask import podtask_bp
from backend.routes.account import account_bp  # Ensure this import is correct
from backend.routes.credits_routes import credits_bp
from backend.routes.team import team_bp
from backend.routes.guest import (
    guest_bp,
)  # Ensure the guest blueprint is correctly imported
from backend.routes.user_to_team import usertoteam_bp
from backend.routes.invitation import invitation_bp
from backend.routes.google_calendar import google_calendar_bp
from backend.routes.episode import episode_bp
from backend.routes.podprofile import podprofile_bp  # Import the podprofile blueprint
from backend.routes.activation import activation_bp, podprofile_initial_bp  # Modified import
from backend.routes.frontend import frontend_bp  # Import the frontend blueprint
from backend.routes.guestpage import guestpage_bp
from backend.routes.guest_to_eposide import guesttoepisode_bp
from backend.routes.guest_form import guest_form_bp  # Import the guest_form blueprint
from backend.utils.email_utils import send_email
from backend.utils.scheduler import start_scheduler
from backend.utils.credit_scheduler import init_credit_scheduler  # Add this import
from backend.routes.billing import billing_bp
from backend.routes.landingpage import landingpage_bp
from dotenv import load_dotenv
from backend.utils import venvupdate
from backend.database.mongo_connection import collection
from backend.routes.Mailing_list import Mailing_list_bp
from backend.routes.user import user_bp
from backend.routes.highlight import highlights_bp
from backend.routes.audio_routes import audio_bp
from backend.routes.video_routes import video_bp
from backend.routes.transcription import transcription_bp
from backend.routes.comment import comment_bp  # Import the comment blueprint
from backend.routes.activity import activity_bp
from backend.routes.stripe_config import stripe_config_bp  # Import the renamed config blueprint
from backend.routes.edit_routes import edit_bp
from backend.routes.enterprise import enterprise_bp  # Import the enterprise blueprint
from backend.routes.lia import lia_bp  # Corrected: Import lia_bp from backend.routes.lia
from backend.routes.index import index_bp # This import is correct

if os.getenv("SKIP_VENV_UPDATE", "false").lower() not in ("true", "1", "yes"):
    venvupdate.update_venv_and_requirements()

load_dotenv()

template_folder = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "frontend", "templates"
)
static_folder = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "frontend", "static"
)

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)


CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://devapp.podmanager.ai",  # Test Branch (testMain)
                "https://app.podmanager.ai",  # Live branch (Main)
                "https://www.podmanager.ai",  # Live branch/index redirect address (Main)
                "http://127.0.0.1:8000",  # Localhost
            ]
        }
    },
)

# These can cause  GET https://app.podmanager.ai/ 503 (Service Unavailable) error in the browser if not set
app.secret_key = os.getenv("SECRET_KEY")
app.config["PREFERRED URL SCHEME"] = "https"

# Register blueprints for different routes
app.register_blueprint(auth_bp)  # Removed url_prefix="/auth"
app.register_blueprint(podcast_bp)  # Register the podcast blueprint
app.register_blueprint(dashboard_bp)
app.register_blueprint(pod_management_bp)
app.register_blueprint(podtask_bp)
app.register_blueprint(team_bp)
app.register_blueprint(Mailing_list_bp)  # <--- Here is the registration
app.register_blueprint(guest_bp)  # Ensure the guest blueprint is correctly registered
app.register_blueprint(guestpage_bp)
app.register_blueprint(account_bp)  # Ensure this registration is correct
app.register_blueprint(credits_bp)
app.register_blueprint(usertoteam_bp)
app.register_blueprint(invitation_bp)
app.register_blueprint(google_calendar_bp)  # Register the google_calendar blueprint
app.register_blueprint(episode_bp)
app.register_blueprint(podprofile_bp)  # Register the podprofile blueprint
app.register_blueprint(activation_bp, url_prefix='/activation')  # Register activation_bp
app.register_blueprint(podprofile_initial_bp, url_prefix='/podprofile')  # <-- This line ensures /podprofile/initial works
app.register_blueprint(frontend_bp)  # Register the frontend blueprint
app.register_blueprint(guesttoepisode_bp)
app.register_blueprint(transcription_bp, url_prefix="/transcription")
app.register_blueprint(audio_bp)
app.register_blueprint(video_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(
    guest_form_bp, url_prefix="/guest-form"
)  # Register the guest_form blueprint with URL prefix
app.register_blueprint(user_bp, url_prefix="/user")
app.register_blueprint(landingpage_bp)
app.register_blueprint(comment_bp)
app.register_blueprint(activity_bp)  # Ensure this registration exists
app.register_blueprint(stripe_config_bp)  # Ensure this registration exists
app.register_blueprint(edit_bp)
app.register_blueprint(enterprise_bp, url_prefix="/enterprise")  # Register the enterprise blueprint
app.register_blueprint(lia_bp, url_prefix="/lia")  # Ensure this line uses the correct lia_bp

# Register the new index blueprint
app.register_blueprint(index_bp) # This registration is correct

# Set the application environment (defaults to production)
APP_ENV = os.getenv("APP_ENV", "production")

# Set the API base URL depending on the environment
API_BASE_URL = os.getenv("API_BASE_URL")

# Initialize colorama
init(autoreset=True)

# Configure logging (ensure this is done before first use)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log messages
logger.info("========================================")
logger.info("✓ Starting server...")
logger.info(f"API Base URL: {os.getenv('API_BASE_URL')}")
logger.info(f"MongoDB URI:  {os.getenv('MONGODB_URI')}")
logger.info("========================================")
logger.info("📧 Email Configuration:")
logger.info(f"EMAIL_USER: {os.getenv('EMAIL_USER', 'Not Set')}")
logger.info(
    f"EMAIL_PASS: {'**** **** **** ****' if os.getenv('EMAIL_PASS') else 'Not Set'}"
)
logger.info("========================================")
logger.info("🚀 Server is running!")
logger.info(
    f"🌐 Local:  {os.getenv('LOCAL_BASE_URL', 'http://127.0.0.1:8000')}"
)
# Append :8000 to the API_BASE_URL for the network log
api_base_url_for_network = os.getenv('API_BASE_URL', 'Not Set')
if api_base_url_for_network != 'Not Set':
    # Simple check to avoid adding port if already present (optional, adjust as needed)
    if ':' not in api_base_url_for_network.split('//')[-1]:
         api_base_url_for_network += ':8000'
logger.info(f"🌐 Network: {api_base_url_for_network}")
logger.info("========================================")


# Log the request with user info
@app.before_request
def load_user():
    # --- Add Log ---
    # Log the raw session object to see its contents
    logger.info(f"Session object before loading user: {dict(session)}")
    # --- End Log ---
    g.user_id = session.get("user_id")
    # Log the result after trying to get user_id
    logger.info(f"Request to {request.path} by user {g.user_id if g.user_id else 'None'}")


start_scheduler(app)
init_credit_scheduler(app)  # Add this line after start_scheduler

# Styled startup message
if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=8000, debug=False
    )  # Ensure the port matches your request URL