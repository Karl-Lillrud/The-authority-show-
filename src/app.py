import os
import logging
from flask import Flask, request, session, g, jsonify, render_template
from flask_cors import CORS
from backend.routes.auth import auth_bp
from backend.routes.forgot_pass import forgotpass_bp
from backend.routes.podcast import podcast_bp  # Import the podcast blueprint
from backend.routes.dashboard import dashboard_bp
from backend.routes.pod_management import pod_management_bp
from backend.routes.podtask import podtask_bp
from backend.routes.account import account_bp
from backend.routes.team import team_bp
from backend.routes.guest import guest_bp
from backend.routes.user_to_team import usertoteam_bp
from backend.routes.invitation import invitation_bp
from backend.routes.google_calendar import google_calendar_bp
from backend.routes.episode import episode_bp
from backend.routes.podprofile import podprofile_bp  # Import the podprofile blueprint
from backend.routes.frontend import frontend_bp  # Import the frontend blueprint
from backend.routes.guestpage import guestpage_bp
from backend.routes.guest_to_eposide import guesttoepisode_bp
from backend.routes.guest_form import guest_form_bp  # Import the guest_form blueprint
from backend.routes.transcription import transcription_bp
from backend.routes.landingpage import landingpage_bp
from dotenv import load_dotenv
from backend.utils import venvupdate
from backend.database.mongo_connection import collection
from backend.utils.email_utils import send_email
from backend.routes.Mailing_list import Mailing_list_bp
from backend.routes.user import user_bp
from backend.routes.audio_routes import audio_bp
from backend.routes.video_routes import video_bp
from backend.routes.highlight import highlights_bp
from transformers import BertForSequenceClassification, AutoTokenizer

# Suppress TensorFlow oneDNN warning by setting the environment variable
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Ensure ffmpeg is installed and available
from pydub import AudioSegment
if not AudioSegment.converter:
    raise RuntimeError("ffmpeg is not installed or not in PATH. Please install it and try again.")

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
                "http://127.0.0.1:8000",  # Localhost
            ]
        }
    },
)

# These can cause  GET https://app.podmanager.ai/ 503 (Service Unavailable) error in the browser if not set
app.secret_key = os.getenv("SECRET_KEY")
app.config["PREFERRED URL SCHEME"] = "https"

# Register blueprints for different routes
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(forgotpass_bp)
app.register_blueprint(podcast_bp)  # Register the podcast blueprint
app.register_blueprint(dashboard_bp)
app.register_blueprint(pod_management_bp)
app.register_blueprint(podtask_bp)
app.register_blueprint(team_bp)
app.register_blueprint(Mailing_list_bp)
app.register_blueprint(guest_bp)
app.register_blueprint(guestpage_bp)
app.register_blueprint(account_bp)
app.register_blueprint(usertoteam_bp)
app.register_blueprint(invitation_bp)
app.register_blueprint(google_calendar_bp)
app.register_blueprint(episode_bp)
app.register_blueprint(podprofile_bp)  # Register the podprofile blueprint
app.register_blueprint(frontend_bp)  # Register the frontend blueprint
app.register_blueprint(guesttoepisode_bp)
app.register_blueprint(guest_form_bp, url_prefix="/guest-form") 
app.register_blueprint(transcription_bp)
app.register_blueprint(audio_bp)
app.register_blueprint(video_bp)
app.register_blueprint(landingpage_bp)

# Set the application environment (defaults to production)
APP_ENV = os.getenv("APP_ENV", "production")

# Set the API base URL depending on the environment
API_BASE_URL = os.getenv("API_BASE_URL")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log the configuration
logger.info(f"API_BASE_URL: {API_BASE_URL}")
logger.info(f"MONGODB_URI: {os.getenv('MONGODB_URI')}")
logger.info(f"APP_ENV: {APP_ENV}")


# Log the request with user info
@app.before_request
def load_user():
    g.user_id = session.get("user_id")
    logger.info(f"Request to {request.path} by user {g.user_id}")


# Initialize the BERT model and tokenizer
model_name = "nreimers/MiniLM-L6-H384-uncased"
model = BertForSequenceClassification.from_pretrained(model_name, num_labels=3)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Define a proper label2id mapping for the BERT model
label2id = {"entailment": 0, "neutral": 1, "contradiction": 2}
model.config.label2id = label2id
model.config.id2label = {v: k for k, v in label2id.items()}

# Run the app
if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=8000, debug=False
    )  # Ensure the port matches your request URL