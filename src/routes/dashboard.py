from flask import g, redirect, render_template, url_for, Blueprint
from database.cosmos_connection import container  # Add import

dashboard_bp = Blueprint("dashboard_bp", __name__)


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
@dashboard_bp.route("/accountsettings", methods=["GET"])
def accountsettings():
    if not g.user_id:
        return redirect(
            url_for("signin_bp.signin")
        )  # Fix: redirect using the blueprint route

    query = "SELECT * FROM c WHERE c.id = @user_id"
    parameters = [{"name": "@user_id", "value": g.user_id}]
    user = list(
        container.query_items(
            query=query, parameters=parameters, enable_cross_partition_query=True
        )
    )[0]
    email = user.get("email", "")
    full_name = user.get("full_name", "")

    return render_template(
        "dashboard/accountsettings.html", email=email, full_name=full_name
    )


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
    return render_template("team/index.html")


@dashboard_bp.route("/guest", methods=["GET", "POST"])
def guest():
    if not g.user_id:
        return redirect(
            url_for("signin_bp.signin")
        )  # Fix: redirect using the blueprint route
    return render_template("guest/index.html")
