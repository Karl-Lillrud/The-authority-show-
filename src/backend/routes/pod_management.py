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
from backend.database.mongo_connection import collection, collection as team_collection

dashboardmanagement_bp = Blueprint("dashboardmanagement_bp", __name__)
pod_management_bp = Blueprint("pod_management_bp", __name__, url_prefix="/podcastmanagement")


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


@pod_management_bp.route("/", methods=["GET"])
def podcast_management():
    """Render the Podcast Management page."""
    return render_template("podcastmanagement/podcastmanagement.html")
