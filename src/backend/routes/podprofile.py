from flask import Blueprint, render_template, session, request, jsonify
from backend.database.mongo_connection import collection
from backend.models.podcasts import PodcastSchema

podprofile_bp = Blueprint('podprofile_bp', __name__)
podcast_schema = PodcastSchema()

@podprofile_bp.route('/podprofile')
def podprofile():
    user_email = session.get('user_email', '')
    return render_template('podprofile/podprofile.html', user_email=user_email)

@podprofile_bp.route('/save_podprofile', methods=['POST'])
def save_podprofile():
    data = request.json
    user_email = session.get('user_email', '')

    # Save to Podcast collection
    podcast_data = {
        "accountId": user_email,
        "podName": data.get("podName"),
        "ownerName": data.get("podOwner"),
        "hostName": data.get("podHost"),
        "rssFeed": data.get("podRss"),
        "googleCal": data.get("googleCal"),
        "guestUrl": data.get("calendarUrl"),
        "socialMedia": [
            data.get("facebook"),
            data.get("instagram"),
            data.get("linkedin"),
            data.get("twitter"),
            data.get("tiktok"),
            data.get("pinterest"),
            data.get("website")
        ],
        "email": data.get("podEmail"),
        "description": data.get("podDescription"),
        "logoUrl": data.get("podProfilePic"),
        "category": data.get("category"),
        "podUrl": data.get("podUrl")
    }
    collection["Podcasts"].insert_one(podcast_data)

    return jsonify({"success": True})
