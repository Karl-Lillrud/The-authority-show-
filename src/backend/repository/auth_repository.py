import uuid
from datetime import datetime
from flask import session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database.mongo_connection import collection
from backend.services.authService import validate_password, validate_email
from backend.repository.usertoteam_repository import UserToTeamRepository
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
        
def register_team_member(self, data):
    try:
        print("🔹 Received registration data:", data)  # Debugging

        # Validate required fields
        required_fields = ["email", "password", "fullName", "phone", "token"]
        for field in required_fields:
            if field not in data or not data[field]:
                print(f"❌ Missing field: {field}")  # Debugging
                return {"error": f"Missing required field: {field}"}, 400

        email = data["email"].lower().strip()
        password = data["password"]
        token = data["token"]

        # Validate email format
        email_error = validate_email(email)
        if email_error:
            print("❌ Email validation failed:", email_error)
            return email_error

        # Validate password strength
        password_error = validate_password(password)
        if password_error:
            print("❌ Password validation failed:", password_error)
            return password_error

        # Validate token and get team information
        invite_record = self.team_invite_collection.find_one({
            "token": token,
            "used": False,
            "expires": {"$gt": datetime.utcnow().isoformat()}
        })
        
        if not invite_record:
            print("❌ Invalid or expired token:", token)
            return {"error": "Invalid or expired invitation token."}, 400
            
        # Make sure the email matches the invited email
        if invite_record["email"].lower() != email:
            print("❌ Email mismatch. Invited:", invite_record["email"], "Registering:", email)
            return {"error": "The email address doesn't match the invitation."}, 400
        
        team_id = invite_record["teamId"]

        # Check if email already exists
        existing_user = self.user_collection.find_one({"email": email})
        if existing_user:
            print("❌ Email already exists:", email)
            return {"error": "Email already registered."}, 409

        # Create user document with team member-specific fields
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

        print("✅ User document to insert:", user_document)  # Debugging

        # Insert the new team member
        self.user_collection.insert_one(user_document)
        print("✅ User successfully inserted into database!")  # Debugging
        
        # Add user to team using the UserToTeamRepository
        user_to_team_data = {
            "userId": user_id,
            "teamId": team_id,
            "role": "member"  # Default role for invited members
        }
        
        # Initialize the UserToTeamRepository
        user_to_team_repo = UserToTeamRepository()
        
        # Add the user to the team
        add_result, status_code = user_to_team_repo.add_user_to_team(user_to_team_data)
        
        if status_code != 201:
            print(f"❌ Failed to add user to team: {add_result}")
            # Rollback user creation
            self.user_collection.delete_one({"_id": user_id})
            return {"error": f"Failed to add user to team: {add_result.get('error', 'Unknown error')}"}, status_code
        
        print("✅ User successfully added to team:", team_id)
        
        # Mark the invitation as used
        self.team_invite_collection.update_one(
            {"token": token},
            {"$set": {"used": True, "usedAt": datetime.utcnow().isoformat()}}
        )
        print("✅ Invitation marked as used")

        return {
            "message": "Team member registration successful!",
            "userId": user_id,
            "redirect_url": url_for("auth_bp.signin", _external=True),
        }, 201

    except Exception as e:
        print("❌ Error during registration:", e)  # Debugging
        logger.error("Error during team member registration: %s", e, exc_info=True)
        return {"error": f"Error during team member registration: {str(e)}"}, 500