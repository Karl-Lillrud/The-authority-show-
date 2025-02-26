from flask import render_template, jsonify, Blueprint, g, request, redirect, url_for, flash
from database.mongo_connection import collection, collection as team_collection

dashboardmanagement_bp = Blueprint("dashboardmanagement_bp", __name__)
pod_management_bp = Blueprint('pod_management', __name__)

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

    # Hämta poddar för just denna användare. 
    # OBS! Använd samma fält som i din DB (du verkar använda "userid" i Podcast-tabellen).
    user_id = str(g.user_id)
    podcasts = list(collection.database.Podcast.find({"userid": user_id}))

    # Om inga poddar
    if len(podcasts) == 0:
        return jsonify({"message": "You have no active or registered podcasts."})

    # Om exakt 1 podd
    if len(podcasts) == 1:
        # Returnera en 'redirect' som din JavaScript kan fånga upp och vidarebefordra
        single_podcast_id = str(podcasts[0]["_id"])
        return jsonify({"redirect": f"/dashboard?podcast_id={single_podcast_id}"})

    # Flera poddar → returnera själva listan
    # Tips: konvertera _id till str om du vill undvika ObjectId i frontend
    for p in podcasts:
        p["_id"] = str(p["_id"])

    return jsonify(podcasts)
