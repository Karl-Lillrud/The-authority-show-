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

@signin_bp.route("/signin", methods=["GET"])



@signin_bp.route("/", methods=["GET"])
def signin_get():
    if request.cookies.get("remember_me") == "true":
        return redirect("/dashboard")
    return render_template("signin.html", API_BASE_URL=API_BASE_URL)


# Add alias for backward compatibility
signin_bp.add_url_rule("/", endpoint="signin", view_func=signin_get)


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

    # Find user by email
    users = collection.database.Users.find_one({"email": email})

    if not users or not check_password_hash(users["passwordHash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Set session data for the logged-in user
    session["user_id"] = str(users["_id"])
    session["user_email"] = users["email"]
    session.permanent = remember

    user_id = session["user_id"]
    podcasts = list(collection.database.Podcast.find({"userid": user_id}))

    # Get user credits
    user_credits = collection.database.Credits.find_one({"user_id": user_id})
    user_credits = user_credits["credits"] if user_credits else 0

    if not podcasts:
        return (
            jsonify({
                "message": "Login successful",
                "redirect_url": "/podprofile",
                "credits": user_credits,
            }),
            200,
        )
    elif len(podcasts) == 1:
        return (
            jsonify({
                "message": "Login successful",
                "redirect_url": "/dashboard",
                "credits": user_credits,
            }),
            200,
        )
    else:
        return (
            jsonify({
                "message": "Login successful",
                "redirect_url": "/homepage",
                "credits": user_credits,
            }),
            200,
        )

    # Response for successful login
    response = jsonify({"message": "Login successful", "redirect_url": "dashboard", "credits": user_credits})

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


@signin_bp.route("/signin", methods=["GET"])
def signin_get_alias():
    return signin_get()
