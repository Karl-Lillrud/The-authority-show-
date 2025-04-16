from flask import (
    render_template,
    jsonify,
    Blueprint,
    g,
    request,
    redirect,
    url_for,
    flash,
)
from backend.database.mongo_connection import database, collection, collection as team_collection
from bson import ObjectId
from datetime import datetime
import logging
import json
import os
from backend.utils.scheduler import render_email_content  # Import the reusable function

dashboardmanagement_bp = Blueprint("dashboardmanagement_bp", __name__)
pod_management_bp = Blueprint("pod_management", __name__)

# Define collections
episode_collection = database["Episodes"]
guest_collection = database["Guests"]


@dashboardmanagement_bp.route("/load_all_guests", methods=["GET"])
def load_all_guests():
    guests = list(collection.find({"type": "guest"}))
    return jsonify(guests)


@dashboardmanagement_bp.route("/profile/<guest_id>", methods=["GET"])
def guest_profile(guest_id):
    guests = (
        load_all_guests().get_json()
    )  # This should return a list/dictionary of guest info.
    guest = next((g for g in guests if g["id"] == guest_id), None)
    if guest is None:
        return "Guest not found", 404
    return render_template("guest/profile.html", guest=guest)


@dashboardmanagement_bp.route("/get_user_podcasts", methods=["GET"])
def get_user_podcasts():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401


@pod_management_bp.route("/invite")
def invite():
    email = request.args.get("email")
    name = request.args.get("name")
    role = request.args.get("role")
    if email and name and role:
        # Add the team member to the database
        team_collection.insert_one(
            {"Email": email, "Name": name, "Role": role, "Status": "Pending"}
        )
        flash("You have successfully joined the team!", "success")
    return redirect(url_for("register_bp.register", email=email))


@pod_management_bp.route("/outbox", methods=["GET"])
def get_outbox():
    podcast_id = request.args.get("podcastId")
    try:
        # Load sent_emails.json
        sent_emails_path = os.path.join(os.path.dirname(__file__), "../../sent_emails.json")
        with open(sent_emails_path, "r") as file:
            sent_emails = json.load(file)

        # Filter emails by podcast ID
        emails = []
        for episode_id, email_data in sent_emails.items():
            if email_data["podcastId"] == podcast_id:
                for trigger_name, is_sent in email_data["triggers"].items():
                    if is_sent:
                        # Fetch the episode
                        episode = episode_collection.find_one({"_id": ObjectId(episode_id)})
                        if not episode:
                            continue

                        # Fetch the guest using the `guid` field
                        guest = guest_collection.find_one({"_id": episode.get("guid")})
                        if not guest:
                            logging.warning(f"No guest found for episode {episode['title']} (GUID: {episode.get('guid')}).")
                        guest_email = guest["email"] if guest else "Unknown"

                        # Render the email content using the reusable function
                        email_content = render_email_content(trigger_name, guest, episode)

                        # Append email details
                        emails.append({
                            "episode_id": episode_id,
                            "trigger_name": trigger_name,
                            "guest_email": guest_email,
                            "subject": f"{trigger_name.capitalize()} Email",
                            "content": email_content,  # Use the rendered email content
                            "timestamp": datetime.now().isoformat()  # Replace with actual timestamp if available
                        })

        return jsonify({"success": True, "data": emails})
    except Exception as e:
        logging.error(f"Error fetching outbox: {str(e)}")
        return jsonify({"success": False, "error": str(e)})
