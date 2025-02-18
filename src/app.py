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
from dotenv import load_dotenv
import os
import logging
from utils import venvupdate
from blueprint_register import register_blueprints

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

app.secret_key = os.getenv("SECRET_KEY")
app.config["PREFERRED URL SCHEME"] = "https"

# Register blueprints dynamically
register_blueprints(app, "routes", [os.path.dirname(__file__) + "/routes"])

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


@app.route("/health")
def health_check():
    logger.info("Health check endpoint called")
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    logger.info("Starting the Flask application")
    app.run(
        host="0.0.0.0", port=8000, debug=False
    )  # Ensure the port matches your request URL and enable debug mode for local environment
