from flask import Blueprint, render_template, session, request, jsonify, current_app
from backend.database.mongo_connection import collection

podprofile_bp = Blueprint("podprofile_bp", __name__)


@podprofile_bp.route("/podprofile")
def podprofile():
    try:
        user_email = session.get("user_email", "")
        return render_template("podprofile/podprofile.html", user_email=user_email)
    except Exception as e:
        current_app.logger.error(f"Error loading podprofile: {e}")
        return "Internal Server Error", 500


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
            "podLogo": data.get("podLogo"),
            "hostName": data.get("hostName"),
            "googleCalendar": data.get("googleCalendar"),
            "calendarUrl": data.get("calendarUrl"),
            "guestForm": data.get("guestForm"),
            "facebook": data.get("facebook"),
            "instagram": data.get("instagram"),
            "linkedin": data.get("linkedin"),
            "twitter": data.get("twitter"),
            "tiktok": data.get("tiktok"),
            "pinterest": data.get("pinterest"),
            "website": data.get("website"),
            "email": data.get("email"),
        }
        collection["User"].insert_one(user_data)

        # Save to Podcast collection
        podcast_data = {
            "UserID": user_email,
            "Podname": data.get("podName"),
            "RSSFeed": data.get("podRss"),
            "GoogleCal": data.get("googleCalendar"),
            "PadURl": data.get("calendarUrl"),
            "GuestURL": data.get("guestForm"),
            "Social_media": {
                "facebook": data.get("facebook"),
                "instagram": data.get("instagram"),
                "linkedin": data.get("linkedin"),
                "twitter": data.get("twitter"),
                "tiktok": data.get("tiktok"),
                "pinterest": data.get("pinterest"),
                "website": data.get("website"),
            },
            "Email": data.get("email"),
        }
        collection["Podcast"].insert_one(podcast_data)

        # Save to Guest collection
        guest_data = {
            "email": data.get("email"),
            "name": data.get("hostName"),
            "description": data.get("guestForm"),
            "linkedin": data.get("linkedin"),
            "twitter": data.get("twitter"),
            "areasOfInterest": [
                data.get("facebook"),
                data.get("instagram"),
                data.get("linkedin"),
                data.get("twitter"),
                data.get("tiktok"),
                data.get("pinterest"),
                data.get("website"),
            ],
            "status": "active",
        }
        collection["Guest"].insert_one(guest_data)

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
