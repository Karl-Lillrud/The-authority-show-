import uuid
from datetime import datetime
from flask import session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database.mongo_connection import collection
from backend.services.authService import validate_password, validate_email
from backend.repository.account_repository import AccountRepository
import logging

logger = logging.getLogger(__name__)

class AuthRepository:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.account_collection = collection.database.Accounts
        self.podcast_collection = collection.database.Podcasts
        self.account_repo = AccountRepository()

    def signin(self, data):
        try:
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            remember = data.get("remember", False)

            user = self.user_collection.find_one({"email": email})
            if not user or not check_password_hash(user["passwordHash"], password):
                return {"error": "Invalid email or password"}, 401

            session["user_id"] = str(user["_id"])
            session["email"] = user["email"]
            session.permanent = remember

            user_account = self.account_collection.find_one({"userId": session["user_id"]})
            if not user_account:
                return {"error": "No account associated with this user"}, 403

            account_id = user_account.get("id", str(user_account["_id"]))
            podcasts = list(self.podcast_collection.find({"accountId": account_id}))

            redirect_url = "/podprofile" if not podcasts else "/podcastmanagement"

            response = {
                "message": "Login successful",
                "redirect_url": redirect_url
            }

            return response, 200

        except Exception as e:
            logger.error("Error during login: %s", e, exc_info=True)
            return {"error": f"Error during login: {str(e)}"}, 500

    def logout(self):
        session.clear()
        response = redirect(url_for("auth_bp.signin"))
        response.delete_cookie("remember_me")
        return response

    def register(self, data):
        try:
            if "email" not in data or "password" not in data:
                return {"error": "Missing email or password"}, 400

            email = data["email"].lower().strip()
            password = data["password"]

            email_error = validate_email(email)
            if email_error:
                return email_error

            password_error = validate_password(password)
            if password_error:
                return password_error

            if self.user_collection.find_one({"email": email}):
                return {"error": "Email already registered."}, 409

            user_id = str(uuid.uuid4())
            hashed_password = generate_password_hash(password)

            user_document = {
                "_id": user_id,
                "email": email,
                "passwordHash": hashed_password,
                "createdAt": datetime.utcnow().isoformat(),
            }

            self.user_collection.insert_one(user_document)

            account_data = {
                "userId": user_id,
                "email": email,
                "companyName": data.get("companyName", ""),
                "isCompany": data.get("isCompany", False),
            }

            account_response, status_code = self.account_repo.create_account(account_data)

            if status_code != 201:
                return {"error": "Failed to create account", "details": account_response}, 500

            account_id = account_response["accountId"]

            return {
                "message": "Registration successful!",
                "userId": user_id,
                "accountId": account_id,
                "redirect_url": url_for("auth_bp.signin", _external=True),
            }, 201

        except Exception as e:
            logger.error("Error during registration: %s", e, exc_info=True)
            return {"error": f"Error during registration: {str(e)}"}, 500
