from flask import Flask, render_template, request, jsonify, session, g
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

# Import Blueprints
from routes import podcast, register, forgot_pass, signin, dashboard, pod_management
from utils import venvupdate

# Load environment variables
load_dotenv()

# Update virtual environment if not skipped
if os.getenv("SKIP_VENV_UPDATE", "false").lower() not in ("true", "1", "yes"):
    venvupdate.update_venv_and_requirements()

# Initialize Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")

# Configure CORS with specific origins
CORS(app, resources={r"/*": {"origins": ["http://192.168.0.4:8000", "https://app.podmanager.ai/"]}})


# Application configuration
app.secret_key = os.getenv("SECRET_KEY")
app.config["PREFERRED_URL_SCHEME"] = "https"
app.config["SECURITY_PASSWORD_SALT"] = os.getenv(

    "SECURITY_PASSWORD_SALT"

)


# Environment setup
APP_ENV = os.getenv("APP_ENV", "production")
API_BASE_URL = "http://127.0.0.1:8000" if APP_ENV == "local" else "https://app.podmanager.ai/"

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register Blueprints
blueprints = [

    register.register_bp,
    forgot_pass.forgotpass_bp,
    signin.signin_bp,
    podcast.podcast_bp,
    dashboard.dashboard_bp,
    pod_management.dashboardmanagement_bp,
    
]
for bp in blueprints:

    app.register_blueprint(bp)

# Middleware to load user session before request
@app.before_request
def load_user():

    g.user_id = session.get("user_id")
    logger.info(f"Request to {request.path} by user {g.user_id}")


# Health check endpoint
@app.route("/health")
def health_check():

    logger.info("Health check endpoint called")
    return jsonify({"status": "healthy"}), 200


# Run the app
if __name__ == "__main__":

    app.run(host="0.0.0.0", port=8000, debug=False)
