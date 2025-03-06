from flask import Blueprint, render_template, g, redirect, url_for, session, request, jsonify, current_app
from backend.database.mongo_connection import collection
import requests

podprofile_bp = Blueprint("podprofile_bp", __name__)

@podprofile_bp.route("/podprofile", methods=["GET"])
def podprofile():
    if not hasattr(g, "user_id") or not g.user_id:
        return redirect(url_for("signin"))

    # Fetch the user's email using the /get_email endpoint
    try:
        response = requests.get(url_for("register_bp.get_email", _external=True), cookies=request.cookies)
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
        }
        collection["User"].insert_one(user_data)

        # Save to Podcast collection
        podcast_data = {
            "UserID": user_email,
            "Podname": data.get("podName"),
            "RSSFeed": data.get("podRss"),
        }
        collection["Podcast"].insert_one(podcast_data)

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
        user_email = session.get("user_email", "")

        if not pod_name or not pod_rss:
            return jsonify({"error": "Missing podcast name or RSS feed"}), 400

        # Save podcast data to the database
        podcast_data = {
            "user_email": user_email,
            "podName": pod_name,
            "podRss": pod_rss,
        }
        collection["Podcasts"].insert_one(podcast_data)

        return jsonify({"redirectUrl": "/podprofile"}), 200
    except Exception as e:
        current_app.logger.error(f"Error posting podcast data: {e}")
        return jsonify({"error": str(e)}), 500
