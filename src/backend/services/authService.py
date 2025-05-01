import logging
import re
import dns.resolver
import random
import hashlib
import uuid
import os
from datetime import datetime, timedelta
from flask import jsonify, session, request, current_app
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from backend.database.mongo_connection import collection
from backend.services.teamService import TeamService
from backend.repository.auth_repository import AuthRepository
from backend.repository.account_repository import AccountRepository
from backend.repository.podcast_repository import PodcastRepository
from backend.repository.user_repository import UserRepository
from backend.repository.episode_repository import EpisodeRepository
from backend.services.activity_service import ActivityService
from backend.utils.blob_storage import upload_file_to_blob
from backend.utils.email_utils import send_login_email
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.auth_repository = AuthRepository()
        self.account_repository = AccountRepository()
        self.podcast_repository = PodcastRepository()
        self.team_service = TeamService()
        self.user_repo = UserRepository()
        self.episode_repo = EpisodeRepository()
        self.activity_service = ActivityService()

    def signin(self, data):
        """Handle login with email and password."""
        try:
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            remember = data.get("remember", False)

            user = self._authenticate_user(email, password)
            if not user:
                logger.warning(f"Invalid login for email {email}.")
                return {"error": "Invalid email or password"}, 401

            self._setup_session(user, remember)
            user_id = session["user_id"]

            account_data = {"ownerId": user_id, "email": email, "isFirstLogin": True}
            account_result, status_code = self.account_repository.create_account(account_data)
            if status_code not in [200, 201]:
                logger.error(f"Failed to create/retrieve account for {email}: {account_result.get('error')}")
                return {"error": account_result.get("error")}, status_code

            team_list = self.team_service.get_user_teams(user_id)
            active_account_id = account_result["accountId"]
            active_account = self.account_repository.get_account(active_account_id)[0]["account"]

            redirect_url = "/podprofile"
            response = {
                "message": "Login successful",
                "redirect_url": redirect_url,
                "teams": team_list,
                "accountId": str(active_account_id),
                "isTeamMember": user.get("isTeamMember", False),
                "usingTeamAccount": False,
            }
            return response, 200

        except Exception as e:
            logger.error(f"Error during login: {e}", exc_info=True)
            return {"error": f"Login error: {str(e)}"}, 500

    def generate_otp(self, email):
        """Generate and store an OTP for a user."""
        try:
            otp = str(random.randint(100000, 999999))
            hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
            expires_at = datetime.utcnow() + timedelta(minutes=10)

            self.user_collection.update_one(
                {"email": email},
                {"$set": {"otp": hashed_otp, "otp_expires_at": expires_at}},
                upsert=True,
            )
            logger.info(f"OTP generated for email {email}.")
            return otp
        except Exception as e:
            logger.error(f"Error generating OTP for {email}: {e}", exc_info=True)
            raise

    def verify_otp_and_login(self, email, otp):
        """Verify OTP and log in the user."""
        try:
            user = self.auth_repository.find_user_by_email(email)
            if not user:
                logger.warning(f"User with email {email} not found.")
                return {"error": "Email not found"}, 404

            hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
            if user.get("otp") != hashed_otp or user.get("otp_expires_at") < datetime.utcnow():
                logger.warning(f"Invalid or expired OTP for email {email}.")
                return {"error": "Invalid or expired OTP"}, 401

            self._setup_session(user, False)
            self.user_collection.update_one({"email": email}, {"$unset": {"otp": "", "otp_expires_at": ""}})
            logger.info(f"User {email} authenticated via OTP.")

            account_data = {
                "ownerId": user["_id"],
                "email": email,
                "isFirstLogin": True,
            }
            account_result, status_code = self.account_repository.create_account(account_data)
            if status_code not in [200, 201]:
                logger.error(f"Failed to create/retrieve account for {email}: {account_result.get('error')}")
                return {"error": account_result.get("error")}, status_code

            return {
                "user_authenticated": True,
                "user": user,
                "accountId": account_result["accountId"],
            }, 200

        except Exception as e:
            logger.error(f"Error verifying OTP for {email}: {e}", exc_info=True)
            return {"error": f"Authentication error: {str(e)}"}, 500

    def verify_login_token(self, token):
        """Verify login token and log in the user."""
        try:
            serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
            email = serializer.loads(token, salt="login-link-salt", max_age=600)

            user = self.auth_repository.find_user_by_email(email)
            if not user:
                user_data = {
                    "_id": str(uuid.uuid4()),
                    "email": email,
                    "createdAt": datetime.utcnow().isoformat(),
                }
                logger.debug(f"Creating new user with data: {user_data}")
                user = self.auth_repository.create_user(user_data)
                if not user:
                    logger.error(f"Failed to create new user for email {email}")
                    return {"error": "Failed to create user"}, 500

            logger.debug(f"User data for token verification: user_id={user['_id']}, email={email}")
            self._setup_session(user, False)

            account_data = {
                "ownerId": user["_id"],
                "email": email,
                "isFirstLogin": True,
            }
            account_result, status_code = self.account_repository.create_account(account_data)
            if status_code not in [200, 201]:
                logger.error(f"Failed to create/retrieve account for {email}: {account_result.get('error')}")
                return {
                    "error": f"Failed to create account: {account_result.get('error')}"
                }, status_code

            logger.info(f"User {email} logged in via token.")

            podcast_data, status_code = self.podcast_repository.get_podcasts(user.get("_id"))
            podcasts = podcast_data.get("podcast", [])
            redirect_url = "/podcastmanagement" if podcasts else "/podprofile"

            return {
                "redirect_url": redirect_url,
                "accountId": account_result["accountId"],
            }, 200

        except SignatureExpired:
            logger.error("Token has expired")
            return {"error": "Token has expired"}, 400
        except BadSignature:
            logger.error("Invalid token")
            return {"error": "Invalid token"}, 400
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}", exc_info=True)
            return {"error": f"Internal server error during token verification: {str(e)}"}, 500

    def _authenticate_user(self, email, password):
        """Authenticate user with email and password."""
        try:
            user = self.auth_repository.find_user_by_email(email)
            if not user or not check_password_hash(user.get("passwordHash", ""), password):
                return None
            return user
        except Exception as e:
            logger.error(f"Authentication error for user {email}: {e}", exc_info=True)
            return None


    def _setup_session(self, user, remember):
        """Set up user session."""
        try:
            session["user_id"] = str(user["_id"])
            session["email"] = user["email"]
            session.permanent = remember
        except Exception as e:
            logger.error(f"Error setting up session for {user['email']}: {e}", exc_info=True)
            raise

def validate_email(self, email):
    """Validate email format and MX record."""
    try:
        email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        if not re.match(email_regex, email):
            return {"error": "Invalid email format."}, 400

        domain = email.split("@")[1]
        answers = dns.resolver.resolve(domain, "MX")
        return None if answers else ({"error": f"Invalid email domain '{domain}'."}, 400)
    except Exception as e:
        logger.error(f"MX lookup failed for domain '{domain}': {e}", exc_info=True)
        return {"error": f"Invalid email domain '{domain}'."}, 400

def validate_password(self, password):
    """Validate password."""
    try:
        if len(password) < 8:
            return {"error": "Password must be at least 8 characters long."}, 400
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            return {"error": "Password must include both letters and numbers."}, 400
        return None
    except Exception as e:
        logger.error(f"Error during password validation: {e}", exc_info=True)
        return {"error": "Error during password validation."}, 400

def get_account_by_user(self, user_id):
    """Retrieve account information by user ID."""
    try:
        response, status_code = self.account_repository.get_account_by_user(user_id)
        if status_code == 200:
            self.activity_service.log_activity(
                user_id=user_id,
                activity_type="account_viewed",
                description="Viewed account details",
                details={"accountId": response.get("account", {}).get("_id")}
            )
        return response, status_code
    except Exception as e:
        logger.error(f"Error retrieving account for user {user_id}: {e}", exc_info=True)
        return {"error": f"Internal server error: {str(e)}"}, 500

def edit_account(self, user_id, data):
    """Update account information."""
    try:
        response, status_code = self.account_repository.edit_account(user_id, data)
        if status_code == 200:
            self.activity_service.log_activity(
                user_id=user_id,
                activity_type="account_updated",
                description="Updated account details",
                details={"updatedFields": list(data.keys())}
            )
        return response, status_code
    except Exception as e:
        logger.error(f"Error updating account for user {user_id}: {e}", exc_info=True)
        return {"error": f"Internal server error: {str(e)}"}, 500

def delete_account(self, user_id):
    """Delete an account and associated data."""
    try:
        podcasts_response, podcasts_status = self.podcast_repository.get_podcasts(user_id)
        if podcasts_status == 200:
            for podcast in podcasts_response.get("podcasts", []):
                delete_podcast_response, delete_podcast_status = self.podcast_repository.delete_podcast(user_id, podcast['_id'])
                if delete_podcast_status != 200:
                    logger.warning(f"Could not delete podcast {podcast['_id']} during account deletion for user {user_id}")

        deleted_account_count = self.account_repository.delete_by_user(user_id)
        if deleted_account_count == 0:
            logger.warning(f"No account document found to delete for user {user_id}")

        user_response, user_status = self.user_repo.delete_user(user_id)
        if user_status != 200:
            logger.error(f"Failed to delete user document for user {user_id}: {user_response.get('error')}")
            return {"error": "Failed to fully delete user data"}, 500

        self.activity_service.log_activity(
            user_id=user_id,
            activity_type="account_deleted",
            description="User account deleted",
            details={}
        )

        return {"message": "Account and associated data deleted successfully"}, 200

    except Exception as e:
        logger.error(f"Error deleting account for user {user_id}: {e}", exc_info=True)
        return {"error": f"Internal server error during account deletion: {str(e)}"}, 500

def upload_profile_picture(self, user_id, file):
    """Upload a profile picture to Azure Blob Storage and update the account."""
    try:
        if not file or not file.filename:
            return {"error": "Invalid file provided"}, 400

        filename = secure_filename(file.filename)
        container_name = "podmanagerfiles"
        blob_path = f"user/{user_id}/profilepicture/{filename}"

        file_url = upload_file_to_blob(container_name, blob_path, file)

        if not file_url:
            return {"error": "Failed to upload profile picture"}, 500

        update_data = {"profilePicUrl": file_url}
        response, status_code = self.edit_account(user_id, update_data)

        if status_code == 200:
            return {
                "message": "Profile picture updated successfully",
                "profilePicUrl": file_url
            }, 200
        else:
            logger.error(f"DB update failed after uploading profile picture for user {user_id}. Blob URL: {file_url}")
            return response, status_code

    except Exception as e:
        logger.error(f"Error uploading profile picture for user {user_id}: {e}", exc_info=True)
        return {"error": f"Internal server error during upload: {str(e)}"}, 500
