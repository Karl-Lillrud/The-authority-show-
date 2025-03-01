from flask import Blueprint, render_template, session, request, jsonify
from backend.database.mongo_connection import collection

podprofile_bp = Blueprint("podprofile_bp", __name__)


@podprofile_bp.route("/podprofile")
def podprofile():
    user_email = session.get("user_email", "")
    return render_template("podprofile/podprofile.html", user_email=user_email)


@podprofile_bp.route("/post_podcast_data", methods=["POST"])
def post_podcast_data():
    data = request.json
    # Process the data and save to the database
    # Example processing code
    if data:
        return jsonify({"redirectUrl": "/some_redirect_url"})
    else:
        return jsonify({"error": "Invalid data"}), 400


@podprofile_bp.route("/save_podprofile", methods=["POST"])
def save_podprofile():
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
