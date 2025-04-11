import logging
from flask import g, redirect, render_template, url_for, Blueprint, request, session, jsonify
from backend.database.mongo_connection import collection
from backend.services.authService import AuthService  # Ensure authService is imported

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize AuthService
authService = AuthService()

dashboard_bp = Blueprint("dashboard_bp", __name__)

# 📌 Dashboard
@dashboard_bp.route("/dashboard", methods=["GET"])
def dashboard():
    """
    Serves the dashboard page if the user is logged in.
    """
    if "user_id" not in session or not session.get("user_id"):
        logger.warning("User is not logged in. Redirecting to sign-in page.")
        return redirect(url_for("auth_bp.signin", error="You must be logged in to access the dashboard."))

    logger.info(f"User {session.get('email', 'Unknown')} accessed the dashboard.")
    return render_template("dashboard/dashboard.html")


# ✅ Serves the homepage page
@dashboard_bp.route("/homepage", methods=["GET"])
def homepage():
    if not g.user_id:
        return redirect(url_for("auth_bp.signin"))  # Updated endpoint

    user_id = str(g.user_id)
    podcasts = list(collection.database.Podcast.find({"userid": user_id}))

    for podcast in podcasts:
        podcast["_id"] = str(podcast["_id"])

    return render_template("dashboard/homepage.html", podcasts=podcasts)


# ✅ Serves the account page
@dashboard_bp.route("/account", methods=["GET"])
def account():
    if not g.user_id:
        return redirect(url_for("auth_bp.signin"))

    user = collection.find_one({"_id": g.user_id})
    email = user.get("email", "") if user else ""
    full_name = user.get("full_name", "") if user else ""
    phone_number = user.get("phone_number", "") if user else ""  # Fetch phone number
    password = user.get("password", "") if user else ""  # Ensure password is hashed

    # Pass all required fields to the account template
    return render_template(
        "account/account.html",
        email=email,
        full_name=full_name,
        phone_number=phone_number,
        password=password,
    )


# ✅ Serves the settings page
@dashboard_bp.route("/settings", methods=["GET"])
def settings():
    if not g.user_id:
        return redirect(url_for("auth_bp.signin"))  # Updated endpoint

    user = collection.find_one({"_id": g.user_id})
    email = user.get("email", "") if user else ""
    full_name = user.get("full_name", "") if user else ""
    phone_number = user.get("phone_number", "") if user else ""  # Fetch phone number
    password = user.get("password", "") if user else ""  # Ensure password is hashed

    # Pass all required fields to the settings template
    return render_template(
        "account/settings.html",
        email=email,
        full_name=full_name,
        phone_number=phone_number,
        password=password,
    )


# ✅ Serves the profile page
@dashboard_bp.route("/podcastmanagement", methods=["GET"])
def podcastmanagement():
    """
    Serves the podcast management page.
    """
    if "user_id" not in session or not session.get("user_id"):
        logger.warning("User is not logged in. Redirecting to sign-in page.")
        logger.debug(f"Session contents: {session}")  # Debug log
        return redirect(url_for("auth_bp.signin", error="You must be logged in to access the dashboard."))
    
    logger.info(f"User {session.get('email', 'Unknown')} accessed the podcast management page.")
    return render_template("podcastmanagement/podcastmanagement.html")


# ✅ Serves the tasks page
@dashboard_bp.route("/taskmanagement", methods=["GET"])
def taskmanagement():
    if not g.user_id:
        return redirect(url_for("auth_bp.signin"))  # Updated endpoint
    return render_template("taskmanagement/taskmanagement.html")


@dashboard_bp.route("/podprofile", methods=["GET", "POST"])
def podprofile():
    """
    Serves the podprofile page.
    """
    if "user_id" not in session or not session.get("user_id"):
        logger.warning("User is not logged in. Redirecting to sign-in page.")
        return redirect(url_for("auth_bp.signin", error="You must be logged in to access this page."))

    logger.info(f"User {session.get('email', 'Unknown')} accessed the podprofile page.")
    return render_template("podprofile/podprofile.html")


@dashboard_bp.route("/team", methods=["GET", "POST"])
def team():
    if not g.user_id:
        return redirect(url_for("auth_bp.signin"))  # Updated endpoint
    return render_template("team/team.html")

@dashboard_bp.route("/register_team_member", methods=["GET"])
def register_team_member():
    """Serves the team member registration page."""
    return render_template("team/register_team_member.html")

@dashboard_bp.route("/addmember", methods=["GET"])
def addmember():
    if not g.user_id:
        return redirect(url_for("auth_bp.signin"))  # Updated endpoint
    return render_template("team/addmember.html")

@dashboard_bp.route("/podcast/<podcast_id>", methods=["GET"])
def podcast(podcast_id):
    if not g.user_id:
        return redirect(url_for("auth_bp.signin"))
    
    # Store podcast_id in session or inject into template if needed
    return render_template("podcast/podcast.html", podcast_id=podcast_id)

@dashboard_bp.route("/get_guests_by_episode/<episode_id>", methods=["GET"])
def get_guests_by_episode(episode_id):
    """
    Fetches guests associated with a specific episode.
    """
    if "user_id" not in session or not session.get("user_id"):
        logger.warning("User is not logged in. Redirecting to sign-in page.")
        return redirect(url_for("auth_bp.signin", error="You must be logged in to access this resource."))

    try:
        # Query the database for guests linked to the given episode ID
        guests = list(collection.database.Guests.find({"episode_id": episode_id}))
        for guest in guests:
            guest["_id"] = str(guest["_id"])  # Convert ObjectId to string for JSON serialization

        logger.info(f"Fetched {len(guests)} guests for episode {episode_id}.")
        return jsonify({"guests": guests}), 200
    except Exception as e:
        logger.error(f"Error fetching guests for episode {episode_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch guests. Please try again later."}), 500
