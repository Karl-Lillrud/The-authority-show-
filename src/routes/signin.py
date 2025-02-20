# 📌 Sign-in Route
from flask import Flask, render_template, request, jsonify, session, Blueprint
from werkzeug.security import check_password_hash
from database.mongo_connection import collection

signin_bp = Blueprint("signin_bp", __name__)


@signin_bp.route("/", methods=["GET"])
@signin_bp.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        return render_template("signin.html")

    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    users = list(collection.find({"email": email}))

    if not users or not check_password_hash(users[0]["passwordHash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = str(users[0]["_id"])
    session["email"] = users[0]["email"]
    session.permanent = True

    # Check the number of podcasts registered
    user_id = session["user_id"]
    podcasts = list(collection.database.Podcast.find({"userid": user_id}))

    if not podcasts:
        return jsonify({
            "message": "Login successful",
            "redirect_url": "/podprofile"
        }), 200
    elif len(podcasts) == 1:
        return jsonify({
            "message": "Login successful",
            "redirect_url": "/dashboard"
        }), 200
    else:
        return jsonify({
            "message": "Login successful",
            "redirect_url": "/homepage"
        }), 200
    
 