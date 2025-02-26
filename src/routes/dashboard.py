from flask import Blueprint, render_template, session, redirect, url_for, g
from database.mongo_connection import users_collection, credits_collection

dashboard_bp = Blueprint("dashboard_bp", __name__)


@dashboard_bp.route("/dashboard", methods=["GET"])
def dashboard():
    if not g.user_id:
        return redirect(url_for("signin_bp.signin"))

    user_email = session.get("email")
    credits = 0
    referral_code = ""
    referrals = 0

    if user_email:
        user = users_collection.find_one({"email": user_email})
        if user:
            referral_code = user.get("referral_code", "")
            user_id = user["_id"]

            credits_data = credits_collection.find_one({"user_id": user_id})
            if credits_data:
                credits = credits_data.get("credits", 0)
                referrals = credits_data.get("referrals", 0)

    return render_template(
        "dashboard/dashboard.html",
        user_email=user_email,
        credits=credits,
        referral_code=referral_code,
        referrals=referrals,
    )


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
        return redirect(url_for("signin_bp.signin"))
    user = users_collection.find_one({"_id": g.user_id})
    email = user.get("email", "") if user else ""
    full_name = user.get("full_name", "") if user else ""
    user_email = session.get("email")
    return render_template(
        "dashboard/settings.html",
        email=email,
        full_name=full_name,
        user_email=user_email,
    )


# ✅ Serves the profile page (podcast management)
@dashboard_bp.route("/podcastmanagement", methods=["GET"])
def podcastmanagement():
    if not g.user_id:
        return redirect(url_for("signin_bp.signin"))
    user_email = session.get("email")
    return render_template("dashboard/podcastmanagement.html", user_email=user_email)


# ✅ Serves the tasks page
@dashboard_bp.route("/taskmanagement", methods=["GET"])
def taskmanagement():
    if not g.user_id:
        return redirect(url_for("signin_bp.signin"))
    user_email = session.get("email")
    return render_template("dashboard/taskmanagement.html", user_email=user_email)


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
        return redirect(url_for("signin_bp.signin"))
    user_email = session.get("email")
    return render_template("team/team.html", user_email=user_email)


@dashboard_bp.route("/guest", methods=["GET", "POST"])
def guest():
    if not g.user_id:
        return redirect(url_for("signin_bp.signin"))
    user_email = session.get("email")
    return render_template("guest/guest.html", user_email=user_email)
