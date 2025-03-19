from flask import (
    Blueprint,
    request,
    jsonify,
    redirect,
    render_template,
)
from werkzeug.security import check_password_hash, generate_password_hash
from backend.repository.auth_repository import AuthRepository
from backend.services.authService import validate_password, validate_email
import os

# Define Blueprint
auth_bp = Blueprint("auth_bp", __name__)

# Instantiate the Auth Repository
auth_repo = AuthRepository()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


@auth_bp.route("/signin", methods=["GET"], endpoint="signin")
@auth_bp.route("/", methods=["GET"])
def signin_page():
    if request.cookies.get("remember_me") == "true":
        return redirect("/dashboard")
    return render_template("signin/signin.html", API_BASE_URL=API_BASE_URL)


@auth_bp.route("/signin", methods=["POST"])
@auth_bp.route("/", methods=["POST"])
def signin_submit():
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    response, status_code = auth_repo.signin(data)
    return jsonify(response), status_code


@auth_bp.route("/logout", methods=["GET"])
def logout_user():
    response = auth_repo.logout()
    return response


@auth_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("register/register.html")


@auth_bp.route("/register", methods=["POST"])
def register_submit():
    if request.content_type != "application/json":
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    response, status_code = auth_repo.register(data)
    return jsonify(response), status_code
