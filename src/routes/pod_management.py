from flask import render_template, jsonify, Blueprint, g
from database.mongo_connection import users_collection, credits_collection, podcasts_collection, guests_collection  # 🔥 Lägg till guests_collection

dashboardmanagement_bp = Blueprint("dashboardmanagement_bp", __name__)

@dashboardmanagement_bp.route("/load_all_guests", methods=["GET"])
def load_all_guests():
    guests = list(guests_collection.find({"type": "guest"}))  # 🔥 Ändrat från collection till guests_collection
    return jsonify(guests)

@dashboardmanagement_bp.route("/profile/<guest_id>", methods=["GET"])
def guest_profile(guest_id):
    guests = load_all_guests().get_json()  # Detta bör returnera en lista/dictionary med gästinfo.
    guest = next((g for g in guests if g["id"] == guest_id), None)
    if guest is None:
        return "Guest not found", 404
    return render_template("guest/profile.html", guest=guest)

@dashboardmanagement_bp.route("/get_user_podcasts", methods=["GET"])
def get_user_podcasts():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    podcasts = list(podcasts_collection.find({"creator_id": g.user_id}))  # 🔥 Ändrat från collection till podcasts_collection
    return jsonify(podcasts)
