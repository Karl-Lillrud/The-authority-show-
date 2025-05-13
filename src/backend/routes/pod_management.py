from flask import (render_template, jsonify, Blueprint, g, request, redirect, url_for, flash)
from backend.database.mongo_connection import database, collection, collection as team_collection
from datetime import datetime
import logging
import json
import os
from backend.utils.scheduler import render_email_content  # Import the reusable function
from backend.utils.trigger_config import TRIGGERS

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


import os
import json

# Define the new paths
BASE_JSON_PATH = os.path.join(os.path.dirname(__file__), "../../Frontend/static/json")
CUSTOM_TRIGGERS_FILE = os.path.join(BASE_JSON_PATH, "custom_triggers.json")
SENT_EMAILS_FILE = os.path.join(BASE_JSON_PATH, "sent_emails.json")

@pod_management_bp.route("/outbox", methods=["GET"])
def get_outbox():
    podcast_id = request.args.get("podcastId")
    try:
        with open(SENT_EMAILS_FILE, "r") as file:
            sent_emails = json.load(file)

        # Filter emails by podcast ID
        emails = []
        for episode_id, email_data in sent_emails.items():
            if email_data["podcastId"] == podcast_id:
                for trigger_name, is_sent in email_data["triggers"].items():
                    if is_sent:
                        # Fetch the episode
                        episode = episode_collection.find_one({"_id": episode_id})
                        if not episode:
                            continue

                        # Fetch the guest using the `guid` field
                        guest = guest_collection.find_one({"_id": episode.get("guid")})
                        guest_email = guest["email"] if guest else "Unknown"

                        # Render the email content dynamically
                        template_path = f"emails/{trigger_name}_email.html"
                        try:
                            email_content = render_template(
                                template_path,
                                guest_name=guest["name"] if guest else "Guest",
                                podName="The Authority Show",
                                episode_title=episode["title"] if episode else "Episode"
                            )
                        except Exception as e:
                            logging.error(f"Error rendering email template {template_path}: {str(e)}")
                            email_content = "Error loading email content."

                        emails.append({
                            "episode_id": episode_id,
                            "trigger_name": trigger_name,
                            "guest_email": guest_email,
                            "subject": f"{trigger_name.replace('_', ' ').title()} Email",
                            "content": email_content,
                            "timestamp": datetime.now().isoformat()
                        })

        return jsonify({"success": True, "data": emails})
    except Exception as e:
        logging.error(f"Error fetching outbox: {str(e)}")
        return jsonify({"success": False, "error": str(e)})


@pod_management_bp.route("/save-trigger", methods=["POST"])
def save_trigger():
    try:
        data = request.get_json()
        podcast_id = data.get("podcast_id")
        trigger_name = data.get("trigger_name")

        if not podcast_id or not trigger_name:
            return jsonify({"success": False, "error": "Missing podcast_id or trigger_name"}), 400

        # Validate the trigger name
        if trigger_name not in TRIGGERS:
            return jsonify({"success": False, "error": "Invalid trigger name"}), 400

        # Use the predefined status and time_check from TRIGGERS
        status = TRIGGERS[trigger_name]["status"]
        time_check = TRIGGERS[trigger_name]["time_check"].total_seconds() if TRIGGERS[trigger_name]["time_check"] else None

        # Load existing custom triggers
        if not os.path.exists(CUSTOM_TRIGGERS_FILE):
            with open(CUSTOM_TRIGGERS_FILE, "w") as file:
                json.dump({}, file)

        with open(CUSTOM_TRIGGERS_FILE, "r") as file:
            custom_triggers = json.load(file)

        # Update the custom triggers for the podcast
        if podcast_id not in custom_triggers:
            custom_triggers[podcast_id] = {}

        custom_triggers[podcast_id][trigger_name] = {
            "status": status,
            "time_check": time_check,
        }

        # Save the updated custom triggers
        with open(CUSTOM_TRIGGERS_FILE, "w") as file:
            json.dump(custom_triggers, file, indent=4)

        return jsonify({"success": True, "message": "Trigger saved successfully."})
    except Exception as e:
        logging.error(f"Error saving custom trigger: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@pod_management_bp.route("/get-trigger-config", methods=["GET"])
def get_trigger_config():
    """Fetch the current trigger configuration for a podcast."""
    try:
        podcast_id = request.args.get("podcastId")
        trigger_name = request.args.get("triggerName")

        # Load existing custom triggers
        if not os.path.exists(CUSTOM_TRIGGERS_FILE):
            return jsonify({"success": True, "data": None})  # No custom triggers exist

        with open(CUSTOM_TRIGGERS_FILE, "r") as file:
            custom_triggers = json.load(file)

        # Get the specific trigger configuration
        trigger_config = custom_triggers.get(podcast_id, {}).get(trigger_name, None)

        return jsonify({"success": True, "data": trigger_config})
    except Exception as e:
        logging.error(f"Error fetching trigger configuration: {str(e)}")
        return jsonify({"success": False, "error": str(e)})
