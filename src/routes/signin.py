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
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    remember = data.get("remember", False)

    # ✅ Corrected user lookup
    users = collection.find_one({"email": email})
    
    # ✅ Proper user validation
    if not users or not check_password_hash(users["passwordHash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    # ✅ Storing session values correctly
    session["user_id"] = str(users["_id"])
    session["email"] = users["email"]
    session.permanent = remember

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
    
 
    response = jsonify({"message": "Login successful", "redirect_url": "dashboard"})
    
    # ✅ Correct cookie handling
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

