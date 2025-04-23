# backend/routes/activity.py
from flask import Blueprint, jsonify, g, session
from backend.database.mongo_connection import collection
import logging

activity_bp = Blueprint("activity_bp", __name__)
logger = logging.getLogger(__name__)


@activity_bp.before_request
def before_request():
    g.user_id = session.get("user_id")


@activity_bp.route("/get_activities", methods=["GET"])
def get_activities():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        activities_collection = collection.database.Activities
        activities = list(
            activities_collection.find({"userId": g.user_id})
            .sort("createdAt", -1)
            .limit(30)  # Increase from 10 to 30
        )
        for activity in activities:
            activity["_id"] = str(activity["_id"])
            activity["createdAt"] = activity["createdAt"].isoformat()
        return jsonify(activities), 200
    except Exception as e:
        logger.error(f"Error retrieving activities: {e}", exc_info=True)
        return jsonify({"error": f"Failed to retrieve activities: {str(e)}"}), 500
