# 📌 Sign-in Route
from flask import Flask, render_template, request, jsonify, session, Blueprint
from werkzeug.security import check_password_hash
from database.mongo_connection import collection
import logging

signin_bp = Blueprint("signin_bp", __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)


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

    logging.debug(f"Attempting to sign in with email: {email}")

    query = {"email": email}
    user = collection.find_one(query)

    if not user:
        logging.debug("User not found")
        return jsonify({"error": "Invalid email or password"}), 401

    if not check_password_hash(user["passwordHash"], password):
        logging.debug("Invalid password")
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = str(user["_id"])
    session["email"] = user["email"]
    session.permanent = True

    logging.debug("Login successful")
    return jsonify({"message": "Login successful", "redirect_url": "dashboard"}), 200
