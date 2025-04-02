import os
import logging
import subprocess
from flask import Flask, request, session, g
from flask_cors import CORS
from dotenv import load_dotenv
from backend.utils import venvupdate

# Import blueprints
from backend.routes.auth import auth_bp
from backend.routes.forgot_pass import forgotpass_bp
from backend.routes.podcast import podcast_bp
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
from backend.routes.podprofile import podprofile_bp
from backend.routes.frontend import frontend_bp
from backend.routes.guestpage import guestpage_bp
from backend.routes.guest_to_eposide import guesttoepisode_bp
from backend.routes.guest_form import guest_form_bp
from backend.routes.transcription import transcription_bp
from backend.routes.landingpage import landingpage_bp
from backend.routes.Mailing_list import Mailing_list_bp
from backend.routes.user import user_bp
from backend.routes.audio_routes import audio_bp
from backend.routes.video_routes import video_bp
from backend.routes.highlight import highlights_bp
from backend.routes.streamlit_proxy import streamlit_proxy_bp  # Import the Streamlit proxy blueprint
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

# Configure app
template_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "frontend", "templates")
static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "frontend", "static")
app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

# Enable CORS
CORS(app, resources={r"/*": {"origins": ["https://devapp.podmanager.ai", "https://app.podmanager.ai", "http://127.0.0.1:8000"]}})

# Set up app config
app.secret_key = os.getenv("SECRET_KEY")
app.config["PREFERRED URL SCHEME"] = "https"

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(forgotpass_bp)
app.register_blueprint(podcast_bp)
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
app.register_blueprint(podprofile_bp)
app.register_blueprint(frontend_bp)
app.register_blueprint(guesttoepisode_bp)
app.register_blueprint(guest_form_bp, url_prefix="/guest-form") 
app.register_blueprint(transcription_bp)
app.register_blueprint(audio_bp)
app.register_blueprint(video_bp)
app.register_blueprint(landingpage_bp)
app.register_blueprint(streamlit_proxy_bp, url_prefix="/streamlit")

# Set environment and log configuration
APP_ENV = os.getenv("APP_ENV", "production")
API_BASE_URL = os.getenv("API_BASE_URL")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"API_BASE_URL: {API_BASE_URL}")
logger.info(f"MONGODB_URI: {os.getenv('MONGODB_URI')}")
logger.info(f"APP_ENV: {APP_ENV}")

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

def start_flask():
    """Start the Flask application."""
    app.run(host="0.0.0.0", port=8000, debug=False)

# Run the app
if __name__ == "__main__":
    try:
        # Start Flask
        start_flask()
        # Start Streamlit (if required, define start_streamlit function)
        # start_streamlit()
    except KeyboardInterrupt:
        # Gracefully handle termination
        logger.info("Shutting down Flask.")
        exit(0)
