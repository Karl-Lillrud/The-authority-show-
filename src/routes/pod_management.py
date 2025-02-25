from flask import render_template, jsonify, Blueprint, g
from database.mongo_connection import collection

dashboardmanagement_bp = Blueprint("dashboardmanagement_bp", __name__)


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