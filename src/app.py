import os
import logging
import subprocess
import requests
from flask import Flask, request, session, g, jsonify, render_template, Response
from flask_cors import CORS
from dotenv import load_dotenv
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

# from backend.routes.transcription import transcription_bp
from backend.routes.landingpage import landingpage_bp
from backend.routes.Mailing_list import Mailing_list_bp
from backend.routes.user import user_bp
from backend.routes.audio_routes import audio_bp
from backend.routes.video_routes import video_bp
from backend.routes.highlight import highlights_bp
from backend.utils import venvupdate
from backend.database.mongo_connection import collection
from backend.utils.email_utils import send_email

# Update virtual environment if required
if os.getenv("SKIP_VENV_UPDATE", "false").lower() not in ("true", "1", "yes"):
    venvupdate.update_venv_and_requirements()

# Load environment variables
load_dotenv()

# Configure Flask app
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
                "https://devapp.podmanager.ai",
                "https://app.podmanager.ai",
                "http://127.0.0.1:8000",
            ]
        }
    },
)

# Set secret key and preferred URL scheme
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
# app.register_blueprint(transcription_bp)
app.register_blueprint(audio_bp)
app.register_blueprint(video_bp)
app.register_blueprint(landingpage_bp)

# Set the application environment
APP_ENV = os.getenv("APP_ENV", "production")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set the API base URL dynamically
if APP_ENV == "production":
    API_BASE_URL = os.getenv("PROD_BASE_URL")
else:
    API_BASE_URL = os.getenv("LOCAL_BASE_URL")

# Log configuration details
logger.info(f"Dynamic API_BASE_URL: {API_BASE_URL}")
logger.info(f"MONGODB_URI: {os.getenv('MONGODB_URI')}")
logger.info(f"APP_ENV: {APP_ENV}")

# Start Streamlit when the app starts
# def start_streamlit():
# Define the Streamlit port, defaulting to 8501
#   streamlit_port = os.getenv("STREAMLIT_PORT", "8501")
# Command to start Streamlit
#  streamlit_command = [
#      "streamlit",
#      "run",
#      "src/backend/routes/transcript/streamlit_transcription.py",  # Adjust the path if needed
#       "--server.port",
#       streamlit_port,
#      "--server.headless",
#       "true",
#   ]
# Start Streamlit as a background process
##    subprocess.Popen(streamlit_command)

# Start Streamlit in the background
# start_streamlit()

# Proxy requests to Streamlit (on port 8501)
# @app.route("/streamlit/<path:path>", methods=["GET", "POST"])
# def proxy_streamlit(path):
#   # Construct the URL for Streamlit
#   url = f"http://localhost:8501/{path}"
#   # Proxy the request to Streamlit
#   resp = requests.request(
#       method=request.method, url=url, headers=request.headers, data=request.data
# )
#   return Response(resp.content, resp.status_code, resp.raw.headers.items())


# Load user information before each request
@app.before_request
def load_user():
    g.user_id = session.get("user_id")
    logger.info(f"Request to {request.path} by user {g.user_id}")


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Ensure Flaqsk rruns on port 8000
    app.run(host="0.0.0.0", port=port)
