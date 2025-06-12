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
        user_email = session.get("email")
        if not user_email:
            current_app.logger.warning(
                "User email not in session for podprofile, redirecting to signin."
            )
            return redirect(url_for("signin"))

        # Calendar connection status is no longer determined here for this page
        return render_template(
            "podprofile/podprofile.html",
            user_email=user_email
            # calendar_connected is removed
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
        # Ensure GOOGLE_REDIRECT_URI in your .env file is correctly set up in your Google Cloud Console
        params = {
            "client_id": getenv("GOOGLE_CLIENT_ID"),
            "redirect_uri": getenv("GOOGLE_REDIRECT_URI"),
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/calendar.events",
            "access_type": "offline",  # To get a refresh token
            "prompt": "consent",  # Optional: forces the consent screen every time, useful for testing refresh token acquisition
        }
        auth_url = f"{calendar_auth_url}?{requests.compat.urlencode(params)}"
        return redirect(auth_url)
    except Exception as e:
        current_app.logger.error(f"Error initiating calendar connection: {e}", exc_info=True)
        # You might want to redirect to an error page or flash a message
        return jsonify({"error": f"Could not connect to calendar service: {str(e)}"}), 500


@podprofile_bp.route("/calendar_callback", methods=["GET"])
def calendar_callback():
    try:
        # Get the code from the request
        code = request.args.get("code")
        if not code:
            current_app.logger.error("Authorization code missing in Google Calendar callback.")
            # Flash a message or redirect to an error page
            return redirect(url_for("pod_management.podcast_management_page", error="calendar_auth_failed"))

        # Get user ID from session
        user_id = session.get("user_id")
        if not user_id:
            current_app.logger.error(
                "User ID not found in session during calendar callback."
            )
            # Flash a message or redirect
            return redirect(url_for("signin_bp.signin_page", error="auth_required"))  # Adjust to your signin route

        # Exchange code for tokens
        token_url = getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")
        data = {
            "code": code,
            "client_id": getenv("GOOGLE_CLIENT_ID"),
            "client_secret": getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": getenv("GOOGLE_REDIRECT_URI"),
            "grant_type": "authorization_code",
        }
        response = requests.post(token_url, data=data)
        response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx or 5xx)
        tokens = response.json()

        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")  # Google often only sends this on the first authorization

        if not access_token:
            current_app.logger.error(f"Access token not found in Google response for user {user_id}. Tokens: {tokens}")
            return redirect(url_for("pod_management.podcast_management_page", error="token_exchange_failed"))

        user_repo = UserRepository()
        # If refresh_token is None, save_tokens should handle it (e.g., not update it if it already exists)
        save_result = user_repo.save_tokens(
            user_id, access_token, refresh_token
        )

        if "error" in save_result:
            current_app.logger.error(f"Error saving Google tokens for user {user_id}: {save_result['error']}")
            return redirect(url_for("pod_management.podcast_management_page", error="token_save_failed"))

        current_app.logger.info(
            f"Successfully saved Google Calendar tokens for user {user_id}."
        )
        flash("Google Calendar connected successfully!", "success")
        # Redirect to the podcast management page where the modal is
        return redirect(url_for("pod_management.podcast_management_page")) 
    except requests.exceptions.HTTPError as http_err:
        current_app.logger.error(f"HTTP error during Google token exchange: {http_err} - Response: {http_err.response.text}", exc_info=True)
        flash("Failed to connect Google Calendar due to a server error.", "error")
        return redirect(url_for("pod_management.podcast_management_page", error="google_server_error"))
    except Exception as e:
        current_app.logger.error(f"Error in Google Calendar callback: {e}", exc_info=True)
        flash("An unexpected error occurred while connecting Google Calendar.", "error")
        return redirect(url_for("pod_management.podcast_management_page", error="calendar_callback_error"))
