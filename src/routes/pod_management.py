from flask import render_template, jsonify, Blueprint, g
from database.mongo_connection import collection

dashboardmanagement_bp = Blueprint("dashboardmanagement_bp", __name__)


@dashboardmanagement_bp.route("/load_all_guests", methods=["GET"])
def load_all_guests():
    query = {"type": "guest"}
    guests = list(collection.find(query))
    return jsonify(guests)


@dashboardmanagement_bp.route("/profile/<guest_id>", methods=["GET"])
def guest_profile(guest_id):
    guests = (
        load_all_guests().get_json()
    )  # This should return a list/dictionary of guest info.
    guest = next((g for g in guests if g["_id"] == guest_id), None)
    if guest is None:
        return "Guest not found", 404
    return render_template("guest/profile.html", guest=guest)


@dashboardmanagement_bp.route("/get_user_podcasts", methods=["GET"])
def get_user_podcasts():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    query = {"creator_id": g.user_id}
    podcasts = list(collection.find(query))
    return jsonify(podcasts)
