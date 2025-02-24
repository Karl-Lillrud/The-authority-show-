# 📌 Sign-in Route
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    Blueprint,
    redirect,
    url_for,
)
from werkzeug.security import check_password_hash
from database.mongo_connection import collection

signin_bp = Blueprint("signin_bp", __name__)


@signin_bp.route("/", methods=["GET"])
@signin_bp.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        if request.cookies.get("remember_me") == "true":
            return redirect("/dashboard")
        return render_template("signin.html")

    if request.content_type != "application/json":
        return (
            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,
        )

    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    remember = data.get("remember", False)

    user = collection.database.Users.find_one({"email": email})

    if not user or not check_password_hash(user["passwordHash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = str(user["_id"])
    session["email"] = user["email"]

    session.permanent = remember

    response = jsonify({"message": "Login successful", "redirect_url": "dashboard"})
    if remember:
        response.set_cookie("remember_me", "true", max_age=30 * 24 * 60 * 60)  # 30 days
    else:
        response.delete_cookie("remember_me")

    return response, 200


@signin_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    response = redirect(url_for("signin_bp.signin"))
    response.delete_cookie("remember_me")
    return response
