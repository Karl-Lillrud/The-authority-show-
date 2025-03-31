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
import json
from datetime import datetime, timezone
from os import getenv  # Add this import

podprofile_bp = Blueprint("podprofile_bp", __name__)


@podprofile_bp.route("/podprofile", methods=["GET"])
def podprofile():
    if not hasattr(g, "user_id") or not g.user_id:
        return redirect(url_for("signin"))

    # Fetch the user's email using the /get_email endpoint
    try:
        response = requests.get(
            url_for("register_bp.get_email", _external=True), cookies=request.cookies
        )
        response.raise_for_status()
        user_email = response.json().get("email")
        if not user_email:
            return redirect(url_for("signin"))
    except requests.RequestException as e:
        current_app.logger.error(f"Error fetching email: {e}")
        return redirect(url_for("signin"))

    session["user_email"] = user_email  # Store the email in the session
    return render_template("podprofile/podprofile.html", user_email=user_email)


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


@podprofile_bp.route("/calendar_callback", methods=["GET"])
def calendar_callback():
    try:
        code = request.args.get("code")
        if not code:
            return jsonify({"error": "Authorization code missing"}), 400

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

        creds = {
            "token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": getenv("GOOGLE_CLIENT_ID"),
            "client_secret": getenv("GOOGLE_CLIENT_SECRET"),
            "scopes": ["https://www.googleapis.com/auth/calendar"]
        }


        print("GOOGLE_CREDS:", json.dumps(creds, indent=2))  # Helpful for .env

        # You could also save this to your DB or file if needed
        session["credentials"] = creds
        return redirect(url_for("podprofile_bp.podprofile"))
    except Exception as e:
        current_app.logger.error(f"Error in calendar callback: {e}")
        return jsonify({"error": str(e)}), 500
