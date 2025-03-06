from flask import g, redirect, render_template, url_for, Blueprint, request, jsonify, session
from backend.database.mongo_connection import collection  # Add import

dashboard_bp = Blueprint("dashboard_bp", __name__)


# 📌 Dashboard
@dashboard_bp.route("/dashboard", methods=["GET"])
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("signin"))
    
    # Get user and credits from the database
    user = collection.database.Users.find_one({"_id": user_id})
    credits = collection.database.Credits.find_one({"user_id": user_id})
    
    # Render dashboard page with credits
    return render_template("dashboard/dashboard.html", user=user, credits=credits)



# ✅ Serves the homepage page
@dashboard_bp.route("/homepage", methods=["GET"])
def homepage():
    if not g.user_id:
        return redirect(url_for("signin_bp.signin"))

    user_id = str(g.user_id)
    podcasts = list(collection.database.Podcast.find({"userid": user_id}))

    for podcast in podcasts:
        podcast["_id"] = str(podcast["_id"])

    return render_template("dashboard/homepage.html", podcasts=podcasts)


# ✅ Serves the settings page
@dashboard_bp.route("/settings", methods=["GET"])
def settings():
    if not g.user_id:
        return redirect(
            url_for("signin_bp.signin")
        )  # Fix: redirect using the blueprint route

    user = collection.find_one({"_id": g.user_id})
    email = user.get("email", "") if user else ""
    full_name = user.get("full_name", "") if user else ""

    return render_template("dashboard/settings.html", email=email, full_name=full_name)


# ✅ Serves the profile page
@dashboard_bp.route("/podcastmanagement", methods=["GET"])
def podcastmanagement():
    if not g.user_id:
        return redirect(
            url_for("signin_bp.signin")
        )  # Fix: redirect using the blueprint route
    return render_template("dashboard/podcastmanagement.html")


# ✅ Serves the tasks page
@dashboard_bp.route("/taskmanagement", methods=["GET"])
def taskmanagement():
    if not g.user_id:
        return redirect(
            url_for("signin_bp.signin")
        )  # Fix: redirect using the blueprint route
    return render_template("dashboard/taskmanagement.html")


@dashboard_bp.route("/podprofile", methods=["GET", "POST"])
def podprofile():
    if not g.user_id:
        return redirect(
            url_for("signin_bp.signin")
        )  # Fix: redirect using the blueprint route
    return render_template("podprofile/podprofile.html")


@dashboard_bp.route("/team", methods=["GET", "POST"])
def team():
    if not g.user_id:
        return redirect(
            url_for("signin_bp.signin")
        )  # Fix: redirect using the blueprint route
    return render_template("team/team.html")


@dashboard_bp.route("/guest", methods=["GET", "POST"])
def guest():
    if not g.user_id:
        return redirect(
            url_for("signin_bp.signin")
        )  # Fix: redirect using the blueprint route
    return render_template("guest/guest.html")
@dashboard_bp.route("/get_credits", methods=["GET"])
def get_credits():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id parameter"}), 400

    user_credits = collection.database.Credits.find_one({"user_id": user_id})
    if not user_credits:
        return jsonify({"error": "User credits not found"}), 404

    return jsonify({
        "credits": user_credits.get("credits", 0),
        "unclaimed_credits": user_credits.get("unclaimed_credits", 0),
        "referral_bonus": user_credits.get("referral_bonus", 0),
        "referrals": user_credits.get("referrals", 0),
        "last_3_referrals": user_credits.get("last_3_referrals", []),
        "vip_status": user_credits.get("vip_status", False),
        "credits_expires_at": user_credits.get("credits_expires_at", ""),
        "episodes_published": user_credits.get("episodes_published", 0),
        "streak_days": user_credits.get("streak_days", 0)
    }), 200
@dashboard_bp.route("/get_user_podcasts", methods=["GET"])
def get_user_podcasts():
    # Dummy implementation; return an empty list or sample data
    return jsonify([])

@dashboard_bp.route("/addmember", methods=["GET"])
def addmember():
    if not g.user_id:
        return redirect(
            url_for("signin_bp.signin")
        )  # Fix: redirect using the blueprint route
    return render_template("team/addmember.html")

