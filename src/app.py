import os
import logging
from flask import Flask, request, session, g, jsonify
from flask_cors import CORS
from backend.database.mongo_connection import collection
from backend.routes.auth import auth_bp
from backend.routes.forgot_pass import forgotpass_bp
from backend.routes.podcast import podcast_bp  # Import the podcast blueprint
from backend.routes.dashboard import dashboard_bp  # Ensure this import is present
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
from backend.routes.guest_to_eposide import guesttoepisode_bp
from backend.routes.credits import credits_bp  # Resolved conflict by adding credits_bp
# from backend.routes.transcription import transcription_bp  # This remains commented
from dotenv import load_dotenv
from backend.utils import venvupdate
from backend.routes.user import user_bp

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
app.register_blueprint(guest_bp)  # Ensure this line is present and has the correct prefix
app.register_blueprint(account_bp)
app.register_blueprint(usertoteam_bp)
app.register_blueprint(invitation_bp)
app.register_blueprint(google_calendar_bp)
app.register_blueprint(episode_bp)
app.register_blueprint(credits_bp)  # Register the credits blueprint
app.register_blueprint(podprofile_bp)
app.register_blueprint(frontend_bp)
app.register_blueprint(guesttoepisode_bp)
# app.register_blueprint(transcription_bp)  # This remains commented
# Set the application environment (defaults to production)
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

@app.context_processor
def inject_user_data():
    user_email = session.get("user_email")
    credits = None
    if user_email:
        user = collection.database.Users.find_one({"email": user_email.lower().strip()})
        if user:
            credits_doc = collection.database.Credits.find_one({"user_id": user["_id"]})
            credits = credits_doc.get("credits", 0) if credits_doc else 0
    return dict(user_email=user_email, credits=credits)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
