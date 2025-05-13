from flask import Blueprint, render_template, session, redirect, url_for, g, request, jsonify
import logging
from backend.database.mongo_connection import collection  # Ensure this import is correct
from backend.repository.podcast_repository import PodcastRepository
from backend.repository.episode_repository import EpisodeRepository

dashboard_bp = Blueprint("dashboard_bp", __name__)
logger = logging.getLogger(__name__)

@dashboard_bp.route("/dashboard", methods=["GET"])
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    # Fetch data for the dashboard
    podcasts = PodcastRepository.get_podcasts_by_user_id(user_id)
    episodes = EpisodeRepository.get_episodes_by_user_id(user_id)

    # Pass data to the frontend
    return render_template(
        "dashboard/dashboard.html",
        podcasts=podcasts or [],
        episodes=episodes or [],
    )

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

    # Pass all required fields to the account template
    return render_template(
        "account/account.html",
        email=email,
        full_name=full_name,
        phone_number=phone_number,
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

    # Pass all required fields to the settings template
    return render_template(
        "account/settings.html",
        email=email,
        full_name=full_name,
        phone_number=phone_number,
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
        return redirect(
            url_for(
                "auth_bp.signin", error="You must be logged in to access the dashboard."
            )
        )

    logger.info(
        f"User {session.get('email', 'Unknown')} accessed the podcast management page."
    )
    return render_template("podcastmanagement/podcastmanagement.html")


# ✅ Serves the tasks page
@dashboard_bp.route("/episode-to-do", methods=["GET"])
def episodetodo():
    if not g.user_id:
        return redirect(url_for("auth_bp.signin"))

    episode_id = request.args.get("episode_id")
    return render_template("episode-to-do/episode-to-do.html", user_id=g.user_id, episode_id=episode_id)


@dashboard_bp.route("/podprofile", methods=["GET", "POST"])
def podprofile():
    """
    Serves the podprofile page.
    """
    if "user_id" not in session or not session.get("user_id"):
        logger.warning("User is not logged in. Redirecting to sign-in page.")
        return redirect(
            url_for(
                "auth_bp.signin", error="You must be logged in to access this page."
            )
        )

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


# ✅ Serves the store page
@dashboard_bp.route("/store", methods=["GET"])
def store():
    """
    Serves the store page.
    """
    if "user_id" not in session or not session.get("user_id"):
        logger.warning("User is not logged in. Redirecting to sign-in page.")
        return redirect(
            url_for(
                "auth_bp.signin", error="You must be logged in to access the store."
            )
        )

    logger.info(f"User {session.get('email', 'Unknown')} accessed the store page.")
    return render_template("store/store.html")
