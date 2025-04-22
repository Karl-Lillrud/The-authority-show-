import os
import logging
from flask import (
    Flask,
    request,
    session,
    g,
    jsonify,
    render_template,
    send_from_directory,
)
from flask_cors import CORS
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
from backend.routes.frontend import frontend_bp
from backend.routes.guestpage import guestpage_bp
from backend.routes.guest_to_eposide import guesttoepisode_bp
from backend.routes.guest_form import guest_form_bp
from backend.services.spotify_integration import file_bp
from backend.routes.transcription import transcription_bp
from backend.utils.email_utils import send_email
from backend.utils.scheduler import start_scheduler
from backend.routes.billing import billing_bp
from backend.routes.landingpage import landingpage_bp
from dotenv import load_dotenv
from backend.utils import venvupdate
from backend.database.mongo_connection import collection
from backend.routes.Mailing_list import Mailing_list_bp
from backend.routes.user import user_bp
# Keep or Uncomment these imports based on requirement
# from backend.routes.highlight import highlights_bp
# from backend.routes.audio_routes import audio_bp
# from backend.routes.video_routes import video_bp

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
                "https://devapp.podmanager.ai", 
                "https://app.podmanager.ai", 
                "http://127.0.0.1:8000", 
            ]
        }
    },
)

app.secret_key = os.getenv("SECRET_KEY")
app.config["PREFERRED URL SCHEME"] = "https"

# Register blueprints for different routes
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
app.register_blueprint(frontend_bp)  
app.register_blueprint(guesttoepisode_bp)
# Uncomment if needed
# app.register_blueprint(transcription_bp, url_prefix="/transcription")
# app.register_blueprint(audio_bp)
# app.register_blueprint(video_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(guest_form_bp, url_prefix="/guest-form")  
app.register_blueprint(user_bp)
app.register_blueprint(landingpage_bp)


# Set the application environment
APP_ENV = os.getenv("APP_ENV", "production")

# Set the API base URL depending on the environment
API_BASE_URL = os.getenv("API_BASE_URL")

# Initialize colorama
init(autoreset=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Styled log messages
logger.info(f"{Fore.GREEN}========================================")
logger.info(f"{Fore.CYAN}✓ Starting server...")
logger.info(f"{Fore.YELLOW}API Base URL: {os.getenv('API_BASE_URL')}")
logger.info(f"{Fore.YELLOW}MongoDB URI:  {os.getenv('MONGODB_URI')}")
logger.info(f"{Fore.GREEN}========================================")
logger.info(f"{Fore.CYAN}📧 Email Configuration:")
logger.info(f"{Fore.BLUE}EMAIL_USER: {os.getenv('EMAIL_USER', 'Not Set')}")
logger.info(
    f"{Fore.BLUE}EMAIL_PASS: {'**** **** **** ****' if os.getenv('EMAIL_PASS') else 'Not Set'}"
)
logger.info(f"{Fore.GREEN}========================================")
logger.info(f"{Fore.CYAN}🚀 Server is running!")
logger.info(
    f"{Fore.MAGENTA}🌐 Local:  {os.getenv('LOCAL_BASE_URL', 'http://127.0.0.1:8000')}"
)
logger.info(f"{Fore.MAGENTA}🌐 Network: http://192.168.0.4:8000")
logger.info(f"{Fore.GREEN}========================================")


@app.before_request
def load_user():
    g.user_id = session.get("user_id")
    logger.info(f"{Fore.BLUE}Request to {request.path} by user {g.user_id}")


start_scheduler(app)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=8000, debug=True
    )  
