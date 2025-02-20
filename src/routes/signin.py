from flask import Flask, render_template, request, jsonify, Blueprint, current_app, redirect, url_for, make_response
from werkzeug.security import check_password_hash
from database.mongo_connection import collection
from itsdangerous import URLSafeTimedSerializer

"""
User Sign-in Module

This module handles user authentication, including:
- Serving the sign-in page (GET request)
- Handling user login (POST request)
- Validating credentials securely
"""

# Define Blueprint for sign-in routes
signin_bp = Blueprint("signin_bp", __name__)

def generate_token(email):

    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt=current_app.config["SECURITY_PASSWORD_SALT"])

def verify_token(token, expiration=3600 * 24 * 30):  # Token valid for 30 days

    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    try:

        email = serializer.loads(

            token, salt=current_app.config["SECURITY_PASSWORD_SALT"], max_age=expiration

        )

    except:

        return False
    
    return email

# User Sign-in Route
@signin_bp.route("/", methods=["GET"])
@signin_bp.route("/signin", methods=["GET", "POST"])
def signin():
    
    if request.method == "GET":

        token = request.cookies.get("remember_token")
        
        if token:

            email = verify_token(token)

            if email:

                user = collection.find_one({"email": email})

                if user:

                    response = make_response(

                        redirect(url_for("dashboard_bp.dashboard"))

                    )
                    response.set_cookie(

                        "user_id",
                        str(user["_id"]),
                        max_age=3600 * 24 * 30,
                        httponly=True,

                    )

                    return response

        return render_template("signin.html")

    if request.content_type != "application/json":
        return (

            jsonify({"error": "Invalid Content-Type. Expected application/json"}),
            415,

        )

    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    remember_me = data.get("remember_me", False)

    print(f"Email: {email}, Remember Me: {remember_me}")  # Debug log

    try:

        users = list(collection.find({"email": email}))

    except Exception as e:

        print(f"Database error: {e}")  # Debug log
        return jsonify({"error": "Database error"}), 500

    if not users or not check_password_hash(users[0]["passwordHash"], password):

        print("Invalid email or password")  # Debug log
        return jsonify({"error": "Invalid email or password"}), 401

    response = jsonify({"message": "Login successful", "redirect_url": "dashboard"})

    if remember_me:

        try:

            token = generate_token(email)
            print(f"Generated Token: {token}")  # Debug log
            response.set_cookie(

                "remember_token", token, max_age=3600 * 24 * 30, httponly=True

            )

            response.set_cookie(

                "user_id", str(users[0]["_id"]), max_age=3600 * 24 * 30, httponly=True

            )
        except Exception as e:

            print(f"Token generation error: {e}")  # Debug log
            return jsonify({"error": "Token generation error"}), 500
        
    else:

        response.set_cookie(

            "user_id", str(users[0]["_id"]), max_age=None, httponly=True

        )

        response.set_cookie("remember_token", "", expires=0)  # Clear any existing token

    return response


@signin_bp.route("/logout", methods=["GET"])
def logout():

    response = redirect(url_for("signin_bp.signin"))
    response.set_cookie("user_id", "", expires=0)
    response.set_cookie("remember_token", "", expires=0)
    return response
