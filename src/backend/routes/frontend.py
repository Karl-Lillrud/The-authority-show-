from flask import Blueprint, render_template, send_from_directory
import os

frontend_bp = Blueprint(
    "frontend", __name__, template_folder="../../frontend/templates"
)


@frontend_bp.route("/podprofile")
def podprofile():
    return render_template("podprofile/podprofile.html")


@frontend_bp.route("/static/<path:filename>")
def static_files(filename):
    static_folder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "../../frontend/static"
    )
    return send_from_directory(static_folder, filename)


@frontend_bp.route("/templates/<path:filename>", endpoint="serve_template")
def template_files(filename):
    template_folder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "../../frontend/templates"
    )
    return send_from_directory(template_folder, filename)


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

@frontend_bp.route("/signup")
def signup_page():
    return render_template("signup/signup.html")
