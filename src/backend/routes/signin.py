from flask import (
    render_template,
    request,
    jsonify,
    session,
    Blueprint,
    redirect,
    url_for,
)
from werkzeug.security import check_password_hash
from backend.database.mongo_connection import collection
import os

signin_bp = Blueprint("signin_bp", __name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# GET route for the root URL renders the signin page
@signin_bp.route("/", methods=["GET"])
def signin_get():
    if request.cookies.get("remember_me") == "true":
        return redirect("/dashboard")
    return render_template("signin.html", API_BASE_URL=API_BASE_URL)

# Explicit GET route for "/signin" to handle redirects properly
@signin_bp.route("/signin", methods=["GET"])
def signin_get_signin():
    return signin_get()

# POST routes for signin
@signin_bp.route("/signin", methods=["POST"])
@signin_bp.route("/", methods=["POST"])
def signin_post():
    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    remember = data.get("remember", False)

    users = collection.find_one({"email": email})

    if not users or not check_password_hash(users["passwordHash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = str(users["_id"])
    session["email"] = users["email"]
    session.permanent = remember

    user_id = session["user_id"]
    podcasts = list(collection.database.Podcast.find({"userid": user_id}))

    if not podcasts:
        redirect_url = "/podprofile"
    elif len(podcasts) == 1:
        redirect_url = "/dashboard"
    else:
        redirect_url = "/homepage"

    response = jsonify({"message": "Login successful", "redirect_url": redirect_url})

    if remember:
        response.set_cookie("remember_me", "true", max_age=30 * 24 * 60 * 60)  # 30 days
    else:
        response.delete_cookie("remember_me")

    return response, 200

@signin_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    response = redirect(url_for("signin_bp.signin_get"))
    response.delete_cookie("remember_me")
    return response
