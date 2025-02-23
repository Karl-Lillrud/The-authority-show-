from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    url_for,
    session,
    redirect,
    g,
    Blueprint,
)
from flask_cors import CORS
from routes.register import register_bp
from routes.forgot_pass import forgotpass_bp
from routes.signin import signin_bp
from routes.podcast import podcast_bp
from routes.dashboard import dashboard_bp
from routes.pod_management import dashboardmanagement_bp
from routes.podtask import podtask_bp
from routes.team import team_bp
from routes.guest import guest_bp
from routes.account import account_bp
from dotenv import load_dotenv
import os
import logging
from utils import venvupdate
from database.mongo_connection import collection as team_collection

# Checking if the environment variable is set to skip the virtual environment update
if os.getenv("SKIP_VENV_UPDATE", "false").lower() not in ("true", "1", "yes"):
    venvupdate.update_venv_and_requirements()

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
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
)  # Enable CORS for specific origins


# These can cause  GET https://app.podmanager.ai/ 503 (Service Unavailable) error in the browser if not set
app.secret_key = os.getenv("SECRET_KEY")
app.config["PREFERRED URL SCHEME"] = "https"
app.register_blueprint(register_bp)
app.register_blueprint(forgotpass_bp)
app.register_blueprint(signin_bp)
app.register_blueprint(podcast_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(dashboardmanagement_bp)
app.register_blueprint(podtask_bp)
app.register_blueprint(team_bp)
app.register_blueprint(guest_bp)
app.register_blueprint(account_bp)

APP_ENV = os.getenv("APP_ENV", "production")  # Default to production

API_BASE_URL = (
    "http://127.0.0.1:8000" if APP_ENV == "local" else "https://app.podmanager.ai/"
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.before_request
def load_user():
    g.user_id = session.get("user_id")
    logger.info(f"Request to {request.path} by user {g.user_id}")
    if g.user_id and request.endpoint not in ("static", "signin_bp.signin"):
        session.permanent = True
    if request.cookies.get("remember_me") == "true" and request.path == "/":
        return redirect("/dashboard")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=8000, debug=True
    )  # Ensure the port matches your request URL
