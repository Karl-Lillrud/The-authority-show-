from flask import (
    g,
    redirect,
    render_template,
    url_for,
    Blueprint,
    request,
    make_response,
)
from database.mongo_connection import collection  # Add import
from .signin import verify_token

dashboard_bp = Blueprint("dashboard_bp", __name__)


@dashboard_bp.before_request
def load_user():
    g.user_id = None
    user_id = request.cookies.get("user_id")
    if user_id:
        g.user_id = user_id
    else:
        token = request.cookies.get("remember_token")
        if token:
            try:
                email = verify_token(token)
                print(f"Verified Email from Token: {email}")  # Debug log
                if email:
                    user = collection.find_one({"email": email})
                    if user:
                        g.user_id = str(user["_id"])
                        print(f"User logged in with token: {g.user_id}")  # Debug log
            except Exception as e:
                print(f"Token verification error: {e}")  # Debug log
        else:
            # Clear cookies if no valid token
            response = make_response(redirect(url_for("signin_bp.signin")))
            response.set_cookie("user_id", "", expires=0)
            response.set_cookie("remember_token", "", expires=0)
            return response


# 📌 Dashboard
@dashboard_bp.route("/dashboard", methods=["GET"])
def dashboard():
    if not g.user_id:
        return redirect(
            url_for("signin_bp.signin")
        )  # Fix: redirect using the blueprint route
    return render_template("dashboard/dashboard.html")


# ✅ Serves the homepage page
@dashboard_bp.route("/homepage", methods=["GET"])
def homepage():
    if not g.user_id:
        return redirect(
            url_for("signin_bp.signin")
        )  # Fix: redirect using the blueprint route
    return render_template("dashboard/homepage.html")


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
    return render_template("podprofile/index.html")


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
