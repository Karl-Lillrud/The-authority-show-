import uuid
from datetime import datetime
from flask import request, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database.mongo_connection import collection
from backend.services.authService import validate_password, validate_email
from backend.repository.account_repository import AccountRepository
from backend.repository.usertoteam_repository import UserToTeamRepository
import logging

logger = logging.getLogger(__name__)

class AuthRepository:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.account_collection = collection.database.Accounts
        self.podcast_collection = collection.database.Podcasts
        self.invite_collection = collection.database.Invites  # ✅ Ensure invites are available
        self.user_to_team_repo = UserToTeamRepository()  # ✅ Initialize UserToTeamRepository
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
        
    def register_team_member(self, data):
        """Registers a new team member from an invite."""
        try:
            print("\U0001F539 Received registration data:", data)  # Debugging

            invite_token = data.get("inviteToken")  # ✅ Now coming from frontend payload

            if not invite_token:
                print("\u274C Missing invite token in request payload.")  # Debugging
                return {"error": "Missing invite token in request."}, 400

            required_fields = ["email", "password", "fullName", "phone"]
            for field in required_fields:
                if field not in data or not data[field]:
                    print(f"\u274C Missing field: {field}")  # Debugging
                    return {"error": f"Missing required field: {field}"}, 400

            email = data["email"].lower().strip()
            password = data["password"]

            invite = self.invite_collection.find_one({"_id": invite_token, "status": "pending"})
            if not invite:
                print(f"\u274C Invalid or expired invite: {invite_token}")
                return {"error": "Invalid or expired invite token."}, 400

            team_id = invite["teamId"]

            if invite["email"].lower() != email:
                print(f"\u274C Email mismatch! Invited: {invite['email']} - Registering: {email}")
                return {"error": "The email does not match the invitation."}, 400

            existing_user = self.user_collection.find_one({"email": email})
            if existing_user:
                print("\u274C Email already exists:", email)
                return {"error": "Email already registered."}, 409

            user_id = str(uuid.uuid4())
            hashed_password = generate_password_hash(password)

            user_document = {
                "_id": user_id,
                "email": email,
                "passwordHash": hashed_password,
                "fullName": data["fullName"],
                "phone": data["phone"],
                "isTeamMember": True,
                "createdAt": datetime.utcnow().isoformat(),
            }

            print("\u2705 User document to insert:", user_document)  # Debugging

            self.user_collection.insert_one(user_document)
            print("\u2705 User successfully inserted into database!")  # Debugging

            user_to_team_data = {
                "userId": user_id,
                "teamId": team_id,
                "role": "member"
            }
            add_result, status_code = self.user_to_team_repo.add_user_to_team(user_to_team_data)

            if status_code != 201:
                print(f"\u274C Failed to add user to team: {add_result}")
                self.user_collection.delete_one({"_id": user_id})
                return {"error": "Failed to add user to team."}, 500

            print(f"\u2705 User successfully linked to team {team_id}")

            self.invite_collection.update_one(
                {"_id": invite_token},
                {"$set": {"status": "accepted", "acceptedAt": datetime.utcnow().isoformat()}}
            )
            print("\u2705 Invitation marked as used")

            return {
                "message": "Team member registration successful!",
                "userId": user_id,
                "redirect_url": url_for("auth_bp.signin", _external=True),
            }, 201

        except Exception as e:
            print("\u274C Error during registration:", e)
            logger.error("Error during team member registration: %s", e, exc_info=True)
            return {"error": f"Error during team member registration: {str(e)}"}, 500
