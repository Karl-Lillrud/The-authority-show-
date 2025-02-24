from flask import Blueprint, jsonify, request, g
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

episodes_bp = Blueprint("episodes_bp", __name__)

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"

client = MongoClient(MONGODB_URI)
database = client[DATABASE_NAME]


@episodes_bp.route("/episodes/count_by_guest/<guest_id>", methods=["GET"])
def count_episodes_by_guest(guest_id):
    try:
        count = database.episodes.count_documents({"guestId": guest_id})
        return jsonify({"count": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
