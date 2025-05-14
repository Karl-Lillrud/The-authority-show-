from flask import Blueprint, redirect, render_template, send_from_directory, request, session
import os

frontend_bp = Blueprint(
    "frontend", __name__, template_folder="../../frontend/templates"
)


@frontend_bp.route("/podprofile")
def podprofile():
    return render_template("podprofile/podprofile.html")


@frontend_bp.route("/beta-email/<path:filename>")
def beta_email_files(filename):
    beta_email_folder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "../../frontend/templates/beta-email",
    )
    return send_from_directory(beta_email_folder, filename)


@frontend_bp.route("/terms-of-service")
def terms_of_service_page():
    return render_template("terms-of-service/terms-of-service.html")


@frontend_bp.route("/privacy-policy")
def privacy_policy_page():
    return render_template("privacy-policy/privacy-policy.html")

@frontend_bp.route("/about")
def about_page():
    return render_template("about/about.html")

@frontend_bp.route("/")
def root():
    if "user_id" in session and session.get("user_id"):
        return redirect("/dashboard")
    if request.cookies.get("remember_me") == "true":
        return redirect("/dashboard")
    return render_template("index/index.html")


