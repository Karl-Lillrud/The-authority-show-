import logging
from flask import Flask, request, session, g
from flask_cors import CORS
from routes.register import register_bp
from routes.forgot_pass import forgotpass_bp
from routes.signin import signin_bp
from routes.podcast import podcast_bp
from routes.dashboard import dashboard_bp
from routes.pod_management import pod_management_bp
from routes.podtask import podtask_bp
from routes.account import account_bp
from routes.team import team_bp
from routes.guest import guest_bp
from routes.userstoteams import userstoteams_bp
from routes.invitation import invitation_bp
from routes.google_calendar import google_calendar_bp
from dotenv import load_dotenv
import os
from utils import venvupdate
from database.mongo_connection import collection as team_collection
from utils.email_utils import send_email
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables
load_dotenv()

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Convert 'createdAt' from string to datetime for comparison
def parse_date(date_str):
    try:
        # Ensure the date is in the correct format and timezone-aware
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
    except ValueError as e:
        # Handle cases where the date format is unexpected
        logger.error(f"Error parsing date: {e}")
        return None

# Function to notify user about data deletion
def notify_user_of_deletion(user_email):
    send_email(
        user_email,
        "Reminder: Data Deletion Notification",
        "Your data will be deleted in 30 days as part of our GDPR compliance."
    )

# GDPR-compliant delete function
def delete_old_users():
    logger.info("Starting the process of deleting old users...")  # Log start

    print("🗑️ Deleting users who haven't logged in for over 1 year...")
    logger.info("Scheduler task started: Deleting old users")

    # Skapa datum för ett år sedan (säkerställ att det är i UTC)
    one_year_ago = (datetime.now(timezone.utc) - timedelta(days=365))

    logger.info(f"One year ago: {one_year_ago}")

    # Hämta användare som inte har loggat in på mer än ett år
    old_users_cursor = team_collection.database.Users.find({"lastLogin": {"$lt": one_year_ago}})

    # Konvertera cursor till lista och kolla om några användare hittades
    old_users = list(old_users_cursor)
    if not old_users:
        logger.info("No users found who haven't logged in for over a year.")
    else:
        for user in old_users:
            user_id = user["_id"]
            user_email = user["email"]
            user_last_login = user.get("lastLogin")  # Kontrollera senaste inloggningstidpunkt

            logger.info(f"User found: {user_email} - Last login at: {user_last_login}")

            # Konvertera 'lastLogin' till timezone-aware datetime om den är naive
            if user_last_login and user_last_login.tzinfo is None:
                user_last_login = user_last_login.replace(tzinfo=timezone.utc)

            # Om användaren inte har loggat in på över ett år, markera för borttagning
            if user_last_login and user_last_login < one_year_ago:
                logger.info(f"Deleting user: {user_email}")

                # Skicka e-postmeddelande om borttagning 30 dagar innan
                try:
                    notify_user_of_deletion(user_email)
                except Exception as e:
                    logger.error(f"Failed to send email to {user_email}: {e}")

                # Ta bort användaren från databasen
                team_collection.database.Users.delete_one({"_id": user_id})

                # Logga borttagningen
                logger.info(f"Deleted user: {user_email}")
            else:
                logger.info(f"User {user_email} has logged in within the last year.")

    logger.info("Scheduler task completed: Finished deleting old users")



# Environment Setup for virtual environment updates
if os.getenv("SKIP_VENV_UPDATE", "false").lower() not in ("true", "1", "yes"):
    venvupdate.update_venv_and_requirements()

# App Configuration
template_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "Frontend", "templates")
static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "Frontend", "static")

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

# CORS Setup
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

# Flask app configuration
app.secret_key = os.getenv("SECRET_KEY")
app.config["PREFERRED_URL_SCHEME"] = "https"

# Register blueprints for different routes
app.register_blueprint(register_bp)
app.register_blueprint(forgotpass_bp)
app.register_blueprint(signin_bp)
app.register_blueprint(podcast_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(pod_management_bp)
app.register_blueprint(podtask_bp)
app.register_blueprint(team_bp)
app.register_blueprint(guest_bp)
app.register_blueprint(account_bp)
app.register_blueprint(userstoteams_bp)
app.register_blueprint(invitation_bp)
app.register_blueprint(google_calendar_bp)

# Scheduler setup for daily checks
scheduler = BackgroundScheduler()


# Schedule deletion of old users every day
scheduler.add_job(delete_old_users, 'interval', days=1)
scheduler.start()


# Test route to manually trigger the delete_old_users function
@app.route("/test-delete-users", methods=["GET"])
def test_delete_users():
    delete_old_users()  # Run the function manually for testing
    return "Old users deletion process executed."

# Log the request with user info
@app.before_request
def load_user():
    g.user_id = session.get("user_id")
    logger.info(f"Request to {request.path} by user {g.user_id}")

# Set the application environment (defaults to production)
APP_ENV = os.getenv("APP_ENV", "production")

# Set the API base URL depending on the environment
API_BASE_URL = (
    "http://127.0.0.1:8000" if APP_ENV == "local" else "https://app.podmanager.ai/"
)

# Run the app
if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=8000, debug=False
    )  # Ensure the port matches your request URL
