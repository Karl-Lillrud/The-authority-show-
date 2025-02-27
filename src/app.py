from flask import Flask, request, session, g, jsonify
from flask_cors import CORS
from backend.routes.register import register_bp
from backend.routes.forgot_pass import forgotpass_bp
from backend.routes.signin import signin_bp
from backend.routes.podcast import podcast_bp  # Import the podcast blueprint
from backend.routes.dashboard import dashboard_bp
from backend.routes.pod_management import pod_management_bp
from backend.routes.podtask import podtask_bp
from backend.routes.account import account_bp
from backend.routes.team import team_bp
from backend.routes.guest import guest_bp
from backend.routes.userstoteams import userstoteams_bp
from backend.routes.invitation import invitation_bp
from backend.routes.google_calendar import google_calendar_bp
from backend.routes.frontend import frontend_bp  # Import the frontend blueprint
from dotenv import load_dotenv
import os
import logging
from backend.utils import venvupdate
from backend.database.mongo_connection import collection
from backend.utils.email_utils import send_email

if os.getenv("SKIP_VENV_UPDATE", "false").lower() not in ("true", "1", "yes"):
    venvupdate.update_venv_and_requirements()

load_dotenv()

template_folder = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "frontend", "templates"
)
static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "frontend", "static")  # Ensure this path is correct

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://192.168.0.4:8000",
                "https://app.podmanager.ai/",
            ]
        }
    },
)

# These can cause  GET https://app.podmanager.ai/ 503 (Service Unavailable) error in the browser if not set
app.secret_key = os.getenv("SECRET_KEY")
app.config["PREFERRED URL SCHEME"] = "https"

# Register blueprints for different routes
app.register_blueprint(register_bp)
app.register_blueprint(forgotpass_bp)
app.register_blueprint(signin_bp)
app.register_blueprint(podcast_bp)  # Register the podcast blueprint
app.register_blueprint(dashboard_bp)
app.register_blueprint(pod_management_bp)
app.register_blueprint(podtask_bp)
app.register_blueprint(team_bp)
app.register_blueprint(guest_bp)
app.register_blueprint(account_bp)
app.register_blueprint(userstoteams_bp)
app.register_blueprint(invitation_bp)
app.register_blueprint(google_calendar_bp)
app.register_blueprint(frontend_bp)  # Register the frontend blueprint

# Set the application environment (defaults to production)
APP_ENV = os.getenv("APP_ENV", "production")

# Set the API base URL depending on the environment
API_BASE_URL = (
    "http://127.0.0.1:8000" if APP_ENV == "local" else "https://app.podmanager.ai/"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Log the request with user info
@app.before_request
def load_user():
    g.user_id = session.get("user_id")
    logger.info(f"Request to {request.path} by user {g.user_id}")


# Run the app
if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=8000, debug=False
    )  # Ensure the port matches your request URL
