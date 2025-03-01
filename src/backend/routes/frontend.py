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


@frontend_bp.route("/templates/<path:filename>")
def template_files(filename):
    template_folder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "../../frontend/templates"
    )
    return send_from_directory(template_folder, filename)


@frontend_bp.route("/images/<path:filename>")
def image_files(filename):
    image_folder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "../../frontend/static/images"
    )
    return send_from_directory(image_folder, filename)


@frontend_bp.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy-policy/privacy-policy.html")


@frontend_bp.route("/terms-of-service")
def terms_of_service():
    return render_template("terms-of-service/terms-of-service.html")
