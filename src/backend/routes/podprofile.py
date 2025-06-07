from flask import (
    Blueprint,
    render_template,
    g,
    redirect,
    url_for,
    session,
    request,
    jsonify,
    current_app,
)
from backend.database.mongo_connection import collection
import requests
from datetime import datetime, timezone
from os import getenv
from backend.repository.user_repository import UserRepository  # Import UserRepository

podprofile_bp = Blueprint("podprofile_bp", __name__)


@podprofile_bp.route("/podprofile", methods=["GET"])
def podprofile():
    if not hasattr(g, "user_id") or not g.user_id:
        return redirect(url_for("signin"))

    try:
        user_email = session.get("email")  # Keep for potential use
        if not user_email:  # Should not happen if g.user_id is set, but good check
            current_app.logger.warning(
                "User email not in session for podprofile, redirecting to signin."
            )
            return redirect(url_for("signin"))

        # Determine if Google Calendar is connected by checking for tokens
        calendar_connected = False
        user_repo = UserRepository()
        user_details = user_repo.get_user_by_id(g.user_id)  # Fetch full user details

        if user_details and user_details.get("google_access_token"):
            calendar_connected = True
            current_app.logger.info(
                f"User {g.user_id} has Google Calendar connected (access token found)."
            )
        else:
            current_app.logger.info(
                f"User {g.user_id} does not have Google Calendar connected (no access token)."
            )

        # The actual podcast data (like pod_rss or googleCal URL)
        # will be fetched by podprofile.js using selectedPodcastId.
        # We only need to pass the connection status for the button logic.
        return render_template(
            "podprofile/podprofile.html",
            user_email=user_email,  # Pass for potential display or other uses
            calendar_connected=calendar_connected,  # Pass OAuth connection status
        )

    except Exception as e:
        current_app.logger.error(
            f"Error in /podprofile route for user {g.user_id}: {e}", exc_info=True
        )
        # Avoid redirecting on all errors, could show a generic error page or message
        return (
            render_template(
                "error_page.html",
                error_message="Could not load podcast profile.",
            ),
            500,
        )


@podprofile_bp.route("/save_podprofile", methods=["POST"])
def save_podprofile():
    try:
        data = request.json
        user_email = session.get("user_email", "")

        # Save to User collection
        user_data = {
            "email": user_email,
            "podName": data.get("podName"),
            "podRss": data.get("podRss"),
            "imageUrl": data.get("imageUrl"),
            "description": data.get("description"),
            "socialMedia": data.get("socialMedia", []),
            "category": data.get("category"),
            "author": data.get("author"),
        }
        collection["Users"].insert_one(user_data)

        # Save to Podcast collection
        podcast_data = {
            "UserID": user_email,
            "Podname": data.get("podName"),
            "RSSFeed": data.get("podRss"),
            "imageUrl": data.get("imageUrl"),
            "description": data.get("description"),
            "socialMedia": data.get("socialMedia", []),
            "category": data.get("category"),
            "author": data.get("author"),
        }
        collection["Podcasts"].insert_one(podcast_data)

        return jsonify({"success": True})
    except Exception as e:
        current_app.logger.error(f"Error saving podprofile: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@podprofile_bp.route("/post_podcast_data", methods=["POST"])
def post_podcast_data():
    try:
        data = request.json
        pod_name = data.get("podName")
        pod_rss = data.get("podRss")
        image_url = data.get("imageUrl")
        description = data.get("description")
        social_media = data.get("socialMedia", [])
        category = data.get("category")
        author = data.get("author")
        episodes = data.get("episodes", [])  # Get episodes data
        user_email = session.get("user_email", "")

        if not pod_name or not pod_rss:
            return jsonify({"error": "Missing podcast name or RSS feed"}), 400

        # Save podcast data to the database
        podcast_data = {
            "user_email": user_email,
            "podName": pod_name,
            "podRss": pod_rss,
            "imageUrl": image_url,
            "description": description,
            "socialMedia": social_media,
            "category": category,
            "author": author,
        }
        result = collection["Podcasts"].insert_one(podcast_data)
        podcast_id = str(result.inserted_id)

        # Save episodes to the Episodes collection
        for episode in episodes:
            episode_data = {
                "podcast_id": podcast_id,
                "title": episode.get("title"),
                "description": episode.get("description"),
                "publishDate": episode.get("pubDate"),
                "duration": episode.get("duration"),
                "audioUrl": episode.get("audioUrl"),
                "fileSize": episode.get("fileSize"),
                "fileType": episode.get("fileType"),
                "guid": episode.get("guid"),
                "season": episode.get("season"),
                "episode": episode.get("episode"),
                "episodeType": episode.get("episodeType"),
                "explicit": episode.get("explicit"),
                "imageUrl": episode.get("imageUrl"),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            collection["Episodes"].insert_one(episode_data)

        return jsonify({"redirectUrl": "/podprofile"}), 200
    except Exception as e:
        current_app.logger.error(f"Error posting podcast data: {e}")
        return jsonify({"error": str(e)}), 500


@podprofile_bp.route("/connect_calendar", methods=["GET"])
def connect_calendar():
    try:
        # Redirect user to the calendar integration service (e.g., Google OAuth)
        calendar_auth_url = getenv("GOOGLE_AUTH_URI")
        params = {
            "client_id": getenv("GOOGLE_CLIENT_ID"),  # Fetch from .env
            "redirect_uri": getenv("GOOGLE_REDIRECT_URI"),  # Fetch from .env
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/calendar.events",
            # https://www.googleapis.com/auth/calendar Main scope for Google Calendar API
            # Can take multiple weeks for access to be granted
            "access_type": "offline",
        }
        auth_url = f"{calendar_auth_url}?{requests.compat.urlencode(params)}"
        return redirect(auth_url)
    except Exception as e:
        current_app.logger.error(f"Error connecting calendar: {e}")
        return jsonify({"error": str(e)}), 500


@podprofile_bp.route("/calendar_callback", methods=["GET"])
def calendar_callback():
    try:
        # Get the code from the request
        code = request.args.get("code")
        if not code:
            current_app.logger.error("Authorization code missing in callback")
            return jsonify({"error": "Authorization code missing"}), 400

        # Get user ID from session
        user_id = session.get("user_id")
        if not user_id:
            current_app.logger.error(
                "User ID not found in session during calendar callback"
            )
            return jsonify({"error": "User not authenticated"}), 401

        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": getenv("GOOGLE_CLIENT_ID"),
            "client_secret": getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": getenv("GOOGLE_REDIRECT_URI"),
            "grant_type": "authorization_code",
        }
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        tokens = response.json()

        # Save tokens to the database using UserRepository
        from backend.repository.user_repository import UserRepository

        user_repo = UserRepository()
        save_result = user_repo.save_tokens(
            user_id, tokens["access_token"], tokens["refresh_token"]
        )

        if "error" in save_result:
            current_app.logger.error(f"Error saving tokens: {save_result['error']}")
            return jsonify(save_result), 500

        current_app.logger.info(
            f"Successfully saved Google Calendar tokens for user {user_id}"
        )
        return redirect(url_for("podprofile_bp.podprofile"))
    except Exception as e:
        current_app.logger.error(f"Error in calendar callback: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
