from flask import Blueprint, request, jsonify, render_template
from database.mongo_connection import collection
import uuid
from datetime import datetime

registerpodcast_bp = Blueprint("registerpodcast_bp", __name__)


@registerpodcast_bp.route("/register_podcast", methods=["GET", "POST"])
def register_podcast():
    if request.method == "GET":
        return render_template("register_podcast.html")

    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    data = request.get_json()
    if "title" not in data or "description" not in data:
        return jsonify({"error": "Missing title or description"}), 400

    title = data["title"].strip()
    description = data["description"].strip()

    podcast_document = {
        "_id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "createdAt": datetime.utcnow().isoformat(),
    }

    try:
        collection.insert_one(podcast_document)
        return jsonify({"message": "Podcast registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
